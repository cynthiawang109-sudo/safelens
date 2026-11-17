import { cp } from "node:fs/promises";
// The standalone server needs its public/static assets alongside server.js.
await cp(
  new URL("../public/", import.meta.url),
  new URL("../.next/standalone/public/", import.meta.url),
  { recursive: true },
);
await cp(
  new URL("../.next/static/", import.meta.url),
  new URL("../.next/standalone/.next/static/", import.meta.url),
  { recursive: true },
);
process.env.HOSTNAME ||= "127.0.0.1";
process.env.PORT ||= "3000";
await import("../.next/standalone/server.js");
