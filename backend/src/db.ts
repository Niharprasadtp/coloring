import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "./generated/prisma/client.js";
import { config } from "./config.js";

// A small pool keeps memory down and stays well under serverless Postgres
// connection limits; the server only runs one image job at a time anyway.
const adapter = new PrismaPg({ connectionString: config.databaseUrl, max: 3, idleTimeoutMillis: 30_000 });

export const prisma = new PrismaClient({ adapter });
