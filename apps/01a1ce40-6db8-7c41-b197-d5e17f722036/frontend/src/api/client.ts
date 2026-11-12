import createClient from "openapi-fetch";
import type { paths } from "./schema";

// Create API client
// The OpenAPI schema already includes the /api prefix in the server URL
const client = createClient<paths>({});

export default client;