#!/usr/bin/env bun

/**
 * Transform OpenAPI types to handle File uploads correctly.
 * This script fixes binary upload schemas that OpenAPI generators otherwise
 * emit as `string` instead of `File` for multipart/form-data uploads.
 */

import fs from 'fs';
import path from 'path';
import ts from 'typescript';
import openapiTS, { astToString } from 'openapi-typescript';
import type { OpenAPI3 } from 'openapi-typescript';

// Check if input file exists
const inputFile: string = path.join(process.cwd(), '../backend/openapi.json');
const outputFile: string = process.argv[2] || './src/api/schema.d.ts';

if (!fs.existsSync(inputFile)) {
  console.error(`Error: OpenAPI schema not found at ${inputFile}`);
  console.error('Run generate-openapi first to create the schema.');
  process.exit(1);
}

// Read OpenAPI schema
const schemaContent: string = fs.readFileSync(inputFile, 'utf-8');
const schema: OpenAPI3 = JSON.parse(schemaContent);

interface OpenAPIDocument {
  paths?: Record<string, unknown>;
  [key: string]: unknown;
}

const multipartFileSchemas = new WeakSet<object>();
const HTTP_METHODS = [
  'get',
  'put',
  'post',
  'delete',
  'options',
  'head',
  'patch',
  'trace'
] as const;

function asObject(value: unknown): Record<string, unknown> | undefined {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return undefined;
  }
  return value as Record<string, unknown>;
}

function resolveLocalReference(
  document: OpenAPIDocument,
  value: unknown
): Record<string, unknown> | undefined {
  const object = asObject(value);
  const reference = object?.$ref;
  if (typeof reference !== 'string' || !reference.startsWith('#/')) {
    return object;
  }

  let resolved: unknown = document;
  for (const rawSegment of reference.slice(2).split('/')) {
    const segment = decodeURIComponent(rawSegment)
      .replaceAll('~1', '/')
      .replaceAll('~0', '~');
    resolved = asObject(resolved)?.[segment];
  }
  return asObject(resolved);
}

function collectSchemaObjects(
  document: OpenAPIDocument,
  value: unknown,
  collected: Set<Record<string, unknown>>,
  visited: Set<Record<string, unknown>>
): void {
  const schemaObject = resolveLocalReference(document, value);
  if (!schemaObject || visited.has(schemaObject)) {
    return;
  }
  visited.add(schemaObject);
  collected.add(schemaObject);

  const properties = asObject(schemaObject.properties);
  if (properties) {
    for (const property of Object.values(properties)) {
      collectSchemaObjects(document, property, collected, visited);
    }
  }

  const patternProperties = asObject(schemaObject.patternProperties);
  if (patternProperties) {
    for (const property of Object.values(patternProperties)) {
      collectSchemaObjects(document, property, collected, visited);
    }
  }

  for (const keyword of [
    'items',
    'prefixItems',
    'allOf',
    'anyOf',
    'oneOf'
  ] as const) {
    const nestedSchemas = schemaObject[keyword];
    if (Array.isArray(nestedSchemas)) {
      for (const nestedSchema of nestedSchemas) {
        collectSchemaObjects(document, nestedSchema, collected, visited);
      }
    } else {
      collectSchemaObjects(document, nestedSchemas, collected, visited);
    }
  }
  collectSchemaObjects(
    document,
    schemaObject.additionalProperties,
    collected,
    visited
  );
}

function markMultipartUploads(document: OpenAPIDocument): void {
  const paths = asObject(document.paths);
  if (!paths) {
    return;
  }

  // FastAPI can reuse one component for multipart and JSON endpoints. Only
  // transform binary leaves that are exclusive to multipart request bodies.
  const multipartSchemas = new Set<Record<string, unknown>>();
  const otherSchemas = new Set<Record<string, unknown>>();
  for (const pathValue of Object.values(paths)) {
    const pathItem = resolveLocalReference(document, pathValue);
    if (!pathItem) {
      continue;
    }
    for (const method of HTTP_METHODS) {
      const operation = resolveLocalReference(document, pathItem[method]);
      const requestBody = resolveLocalReference(document, operation?.requestBody);
      const content = asObject(requestBody?.content);
      if (content) {
        for (const [mediaType, mediaValue] of Object.entries(content)) {
          const media = resolveLocalReference(document, mediaValue);
          collectSchemaObjects(
            document,
            media?.schema,
            mediaType === 'multipart/form-data'
              ? multipartSchemas
              : otherSchemas,
            new Set()
          );
        }
      }

      const responses = asObject(operation?.responses);
      if (responses) {
        for (const responseValue of Object.values(responses)) {
          const response = resolveLocalReference(document, responseValue);
          const responseContent = asObject(response?.content);
          if (!responseContent) {
            continue;
          }
          for (const mediaValue of Object.values(responseContent)) {
            const media = resolveLocalReference(document, mediaValue);
            collectSchemaObjects(
              document,
              media?.schema,
              otherSchemas,
              new Set()
            );
          }
        }
      }
    }
  }

  for (const schemaObject of multipartSchemas) {
    if (
      !otherSchemas.has(schemaObject) &&
      (schemaObject.format === 'binary' ||
        schemaObject.contentMediaType === 'application/octet-stream')
    ) {
      multipartFileSchemas.add(schemaObject);
    }
  }
}

// Generate TypeScript types with transforms for OpenAPI 3.0 and 3.1 binaries.
async function generateTypes(): Promise<void> {
  try {
    markMultipartUploads(schema as unknown as OpenAPIDocument);
    const ast = await openapiTS(schema, {
      transform(schemaObject): ts.TypeNode | undefined {
        // FastAPI emits contentMediaType for UploadFile under OpenAPI 3.1;
        // older OpenAPI 3.0 schemas use format: binary.
        if (multipartFileSchemas.has(schemaObject)) {
          // Return a TypeScript AST node for the File type
          return ts.factory.createTypeReferenceNode(
            ts.factory.createIdentifier('File'),
            undefined
          );
        }
        return undefined;
      }
    });

    // Convert AST to string
    const output: string = astToString(ast);

    // Write to the output file
    fs.writeFileSync(outputFile, output);
    console.log(`✓ TypeScript types generated at ${outputFile}`);
    console.log('✓ Binary upload fields transformed to File type');
  } catch (error) {
    console.error('Error generating types:', error);
    process.exit(1);
  }
}

generateTypes();
