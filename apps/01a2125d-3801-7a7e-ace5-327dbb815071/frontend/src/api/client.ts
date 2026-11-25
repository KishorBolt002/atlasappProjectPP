import createClient from "openapi-fetch";
import type { paths } from "./schema";
import { reloadOnSignedOut } from "./session";

// Create API client
// Spec paths are the full request paths, /api prefix included, so the client
// takes no base URL.
const client = createClient<paths>({});
client.use({
  onResponse: ({ request, response }) => reloadOnSignedOut(request, response),
});

export default client;