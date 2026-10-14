"use client";

import { useEffect, useState } from "react";
import { useAuthStore, type Perfil } from "./auth-store";

/** Perfil del store zustand; `cargado` evita hydration mismatch (SSR = false). */
export function usePerfil(): { perfil: Perfil | null; cargado: boolean } {
  const perfil = useAuthStore((s) => s.perfil);
  const [cargado, setCargado] = useState(false);
  useEffect(() => {
    setCargado(true);
  }, []);
  return { perfil, cargado };
}
