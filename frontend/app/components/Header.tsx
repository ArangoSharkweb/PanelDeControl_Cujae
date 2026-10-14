"use client";

import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select";

interface Props {
  busqueda: string;
  onBusqueda: (v: string) => void;
  proceso: string;
  onProceso: (v: string) => void;
  procesos: { id: string; nombre: string }[];
  vista: "general" | "procesos";
  onVista: (v: "general" | "procesos") => void;
  onActualizar: () => void;
  onExportar: () => void;
}

export default function Header({
  busqueda,
  onBusqueda,
  proceso,
  onProceso,
  procesos,
  vista,
  onVista,
  onActualizar,
  onExportar,
}: Props) {
  return (
    <header className="bg-card border-b border-border px-6 py-3 flex flex-wrap items-center gap-3 sticky top-0 z-10">
      <Input
        value={busqueda}
        onChange={(e) => onBusqueda(e.target.value)}
        placeholder="Buscar indicador..."
        className="w-64"
      />
      <Select value={proceso || "todos"} onValueChange={(v) => onProceso(v === "todos" ? "" : v)}>
        <SelectTrigger className="w-56">
          <SelectValue placeholder="Todos los procesos" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="todos">Todos los procesos</SelectItem>
          {procesos.map((p) => (
            <SelectItem key={p.id} value={p.id}>
              {p.nombre}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <div className="flex rounded-lg overflow-hidden border border-input">
        <Button
          variant={vista === "general" ? "default" : "outline"}
          size="sm"
          className="rounded-none"
          onClick={() => onVista("general")}
        >
          Vista general
        </Button>
        <Button
          variant={vista === "procesos" ? "default" : "outline"}
          size="sm"
          className="rounded-none"
          onClick={() => onVista("procesos")}
        >
          Por procesos
        </Button>
      </div>
      <Button variant="outline" size="sm" onClick={onActualizar}>
        Actualizar
      </Button>
      <Button size="sm" onClick={onExportar}>
        Exportar Excel
      </Button>
    </header>
  );
}
