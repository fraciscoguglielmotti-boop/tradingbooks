import { z } from "zod";

/**
 * Validación de env vars en runtime (server-side).
 *
 * Importar desde código que corre en el servidor:
 *   import { env } from "@/lib/env";
 *
 * Si una var requerida falta, la app falla en arranque con mensaje claro
 * en lugar de fallar silenciosamente con un error 500 al primer request.
 *
 * Las vars ANTHROPIC_API_KEY y SUPABASE_SERVICE_ROLE_KEY son opcionales
 * acá porque algunas rutas (auth, lectura pública) funcionan sin ellas.
 * Las features que las requieren validan su presencia en sitio.
 */

const schema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url().optional(),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1).optional(),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(1).optional(),
  ANTHROPIC_API_KEY: z.string().min(1).optional(),
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
});

const parsed = schema.safeParse(process.env);

if (!parsed.success) {
  console.error("[env] Variables inválidas:", z.treeifyError(parsed.error));
  throw new Error("Variables de entorno inválidas — ver logs.");
}

export const env = parsed.data;

/**
 * Helper para features que SÍ requieren una var puntual: lanza un error
 * descriptivo si está vacía. Usar al borde, ej. al instanciar el cliente.
 */
export function requireEnv<K extends keyof typeof env>(key: K): NonNullable<(typeof env)[K]> {
  const value = env[key];
  if (value == null || value === "") {
    throw new Error(
      `[env] Falta la variable ${String(key)}. Definila en .env.local`,
    );
  }
  return value as NonNullable<(typeof env)[K]>;
}
