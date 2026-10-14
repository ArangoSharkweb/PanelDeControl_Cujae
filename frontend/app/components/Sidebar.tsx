"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/app/lib/auth-store";
import { puedeAlguno } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Button } from "@/app/components/ui/button";

interface Modulo {
  href: string;
  label: string;
  permisos: string[];
}

const MODULOS: Modulo[] = [
  { href: "/", label: "Tablero general", permisos: ["tablero"] },
  { href: "/indicadores", label: "Indicadores de gestion", permisos: ["indicadores"] },
  { href: "/objetivos", label: "Objetivos estrategicos", permisos: ["tablero", "indicadores"] },
  { href: "/procesos", label: "Procesos institucionales", permisos: ["tablero", "indicadores"] },
  { href: "/metricas", label: "Metricas por proceso", permisos: ["tablero", "indicadores"] },
  { href: "/cursos", label: "Cursos academicos", permisos: ["tablero", "indicadores"] },
  { href: "/unidades", label: "Unidades organizativas", permisos: ["tablero", "indicadores"] },
  { href: "/usuarios", label: "Administracion de usuarios", permisos: ["usuarios"] },
  { href: "/calculo", label: "Calculo de indicadores", permisos: ["config"] },
  { href: "/fuentes", label: "Fuentes de datos", permisos: ["fuentes"] },
  { href: "/auditoria", label: "Auditoria del sistema", permisos: ["auditoria"] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { perfil, cargado } = usePerfil();

  const cerrarSesion = () => {
    useAuthStore.getState().cerrarSesion();
    router.push("/login");
  };

  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-cujae text-white flex flex-col">
      <div className="px-5 py-5 border-b border-green-700">
        <div className="text-lg font-bold">CUJAE</div>
        <div className="text-xs text-green-100">Cuadro de Mando Institucional</div>
      </div>
      <nav className="flex-1 overflow-y-auto py-3">
        {cargado &&
          MODULOS.filter((m) => puedeAlguno(m.permisos)).map((m) => (
            <Link
              key={m.href}
              href={m.href}
              className={`block px-5 py-2.5 text-sm hover:bg-green-700 transition ${
                pathname === m.href ? "bg-green-800 font-semibold" : ""
              }`}
            >
              {m.label}
            </Link>
          ))}
      </nav>
      <div className="border-t border-green-700 p-4 flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-white text-cujae font-bold flex items-center justify-center">
          {cargado && perfil ? perfil.username[0]?.toUpperCase() : "?"}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold truncate">
            {cargado && perfil ? perfil.username : "Invitado"}
          </div>
          <div className="text-xs text-green-100">
            {cargado && perfil ? `${perfil.rol} · ${perfil.auth_type}` : "-"}
          </div>
        </div>
        <Button
          onClick={cerrarSesion}
          title="Cerrar sesion"
          variant="secondary"
          size="sm"
          className="bg-green-900 text-white hover:bg-green-950 hover:text-white text-xs"
        >
          Salir
        </Button>
      </div>
    </aside>
  );
}
