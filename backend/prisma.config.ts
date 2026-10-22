import "dotenv/config";
import { defineConfig, env } from "prisma/config";

// Used by the Prisma CLI only (generate / migrate). Migrations need a direct,
// non-pooled connection; the running server uses the pooled DATABASE_URL.
export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: { path: "prisma/migrations" },
  datasource: { url: env("DIRECT_URL") },
});
