const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

import { useAuthStore, type Perfil } from "./auth-store";

export type { Perfil } from "./auth-store";

export interface Rol {
  rol: string;
}

export interface Indicador {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  periodicidad: string;
  sentido: string;
  formula: string | null;
  proceso_id: string;
  nivel: string;
  esencial: boolean;
  activo: boolean;
  metas?: Meta[];
  variables?: Variable[];
}

export interface Meta {
  id: string;
  curso_id: string;
  valor_meta: string;
  umbral_verde: string;
  umbral_amarillo: string;
}

export interface Variable {
  id: string;
  nombre: string;
  tabla: string | null;
  columna: string | null;
  funcion_agregacion: string | null;
}

export interface Valor {
  id: string;
  indicador_id: string;
  valor: string | null;
  estado_semaforo: "verde" | "amarillo" | "rojo" | null;
  porcentaje_meta: string | null;
  calculado_en: string | null;
}

export interface SecurityLog {
  log_id: string;
  ts: string;
  event_type: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  usuario: { username?: string; role?: string };
  session: { ip_address?: string };
  action: { resource_type?: string; operation?: string };
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return useAuthStore.getState().token;
}

export function getPerfil(): Perfil | null {
  if (typeof window === "undefined") return null;
  return useAuthStore.getState().perfil;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (res.status === 401 && typeof window !== "undefined") {
    useAuthStore.getState().cerrarSesion();
    window.location.href = "/login";
    throw new Error("No autorizado");
  }
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const SEMAFORO_COLOR: Record<string, string> = {
  verde: "#16a34a",
  amarillo: "#f59e0b",
  rojo: "#dc2626",
};

export const TIPO_BADGE: Record<string, string> = {
  rectorado: "bg-red-100 text-red-700",
  direccion: "bg-orange-100 text-orange-700",
  vicerrectorado: "bg-purple-100 text-purple-700",
  facultad: "bg-blue-100 text-blue-700",
  proceso: "bg-green-100 text-green-700",
};

// Matriz RBAC (RF-04) — espejo de backend/app/security/rbac.py
export const RBAC: Record<string, string[]> = {
  administrador: ["usuarios", "catalogos", "fuentes", "config", "recalcular", "logs"],
  alta_direccion: ["tablero", "indicadores", "fuentes", "config", "recalcular", "logs"],
  directivo: ["tablero", "indicadores"],
  jefe_proceso: ["tablero", "indicadores", "cargar_datos"],
  auditor: ["tablero", "indicadores", "auditoria", "logs"],
};

export function puede(permiso: string): boolean {
  const perfil = getPerfil();
  if (!perfil) return false;
  return (RBAC[perfil.rol] ?? []).includes(permiso);
}

export function puedeAlguno(permisos: string[]): boolean {
  return permisos.some((p) => puede(p));
}
