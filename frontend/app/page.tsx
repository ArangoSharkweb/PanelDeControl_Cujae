"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/app/components/Sidebar";
import Header from "@/app/components/Header";
import IndicatorCard from "@/app/components/IndicatorCard";
import { EstadoGeneral, GaugeEsenciales } from "@/app/components/Widgets";
import { api, getPerfil, getToken, puede, type Indicador, type Valor } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Card } from "@/app/components/ui/card";
import { Skeleton } from "@/app/components/ui/skeleton";

interface Proceso {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string;
}

interface Curso {
  id: string;
  nombre: string;
  es_curso_actual: boolean;
}

type IndicadorConValor = {
  indicador: Indicador;
  valor: Valor | null;
  meta: string;
  procesoNombre: string;
  procesoTipo: string;
};

export default function Dashboard() {
  const router = useRouter();
  const [indicadores, setIndicadores] = useState<Indicador[]>([]);
  const [procesos, setProcesos] = useState<Proceso[]>([]);
  const [cursos, setCursos] = useState<Curso[]>([]);
  const [valores, setValores] = useState<Record<string, Valor>>({});
  const [busqueda, setBusqueda] = useState("");
  const [proceso, setProceso] = useState("");
  const [vista, setVista] = useState<"general" | "procesos">("general");
  const [cargando, setCargando] = useState(true);
  const { cargado } = usePerfil();

  const cargar = async () => {
    setCargando(true);
    try {
      const [inds, procs, curs] = await Promise.all([
        api<Indicador[]>("/indicadores"),
        api<Proceso[]>("/catalogos/procesos"),
        api<Curso[]>("/catalogos/cursos"),
      ]);
      setIndicadores(inds);
      setProcesos(procs);
      setCursos(curs);

      const mapa: Record<string, Valor> = {};
      await Promise.all(
        inds.map(async (i) => {
          try {
            const vals = await api<Valor[]>(`/indicadores/${i.id}/valores`);
            const vigente = vals.find((v) => v);
            if (vigente) mapa[i.id] = vigente;
          } catch {
            /* aislamiento de fallos por indicador */
          }
        })
      );
      setValores(mapa);
    } catch {
      /* sin datos */
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    if (!puede("tablero")) {
      setCargando(false);
      if (getPerfil()?.rol === "administrador") router.replace("/usuarios");
      return;
    }
    void cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cursoActual = cursos.find((c) => c.es_curso_actual)?.nombre ?? "Curso actual";

  const items: IndicadorConValor[] = useMemo(() => {
    return indicadores
      .filter((i) => (proceso ? i.proceso_id === proceso : true))
      .filter((i) =>
        busqueda
          ? (i.nombre + i.codigo).toLowerCase().includes(busqueda.toLowerCase())
          : true
      )
      .map((i) => {
        const p = procesos.find((pr) => pr.id === i.proceso_id);
        return {
          indicador: i,
          valor: valores[i.id] ?? null,
          meta: i.metas?.[0]?.valor_meta ?? "--",
          procesoNombre: p?.nombre ?? "Sin proceso",
          procesoTipo: p?.tipo ?? "proceso",
        };
      });
  }, [indicadores, procesos, valores, proceso, busqueda]);

  const distribucion = useMemo(() => {
    const counts = { verde: 0, amarillo: 0, rojo: 0 };
    items.forEach((it) => {
      const e = it.valor?.estado_semaforo;
      if (e === "verde" || e === "amarillo" || e === "rojo") counts[e] += 1;
    });
    return Object.entries(counts).map(([estado, cantidad]) => ({ estado, cantidad }));
  }, [items]);

  const pctEsenciales = useMemo(() => {
    const esenciales = items.filter((i) => i.indicador.esencial);
    if (esenciales.length === 0) return 0;
    const cumplidos = esenciales.filter((e) => e.valor?.estado_semaforo === "verde").length;
    return Math.round((cumplidos / esenciales.length) * 100);
  }, [items]);

  const exportar = async () => {
    const filas = items.map((it) => ({
      Codigo: it.indicador.codigo,
      Nombre: it.indicador.nombre,
      Proceso: it.procesoNombre,
      Valor: it.valor?.valor ?? "",
      Meta: it.meta,
      Estado: it.valor?.estado_semaforo ?? "",
      Curso: cursoActual,
    }));
    const csv = [
      Object.keys(filas[0] ?? {}).join(","),
      ...filas.map((f) => Object.values(f).map((v) => `"${v}"`).join(",")),
    ].join("\n");
    const blob = new Blob([`﻿${csv}`], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "indicadores.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const porProceso = useMemo(() => {
    const grupos = new Map<string, IndicadorConValor[]>();
    items.forEach((it) => {
      const arr = grupos.get(it.procesoNombre) ?? [];
      arr.push(it);
      grupos.set(it.procesoNombre, arr);
    });
    return Array.from(grupos.entries());
  }, [items]);

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-64">
        <Header
          busqueda={busqueda}
          onBusqueda={setBusqueda}
          proceso={proceso}
          onProceso={setProceso}
          procesos={procesos.map((p) => ({ id: p.id, nombre: p.nombre }))}
          vista={vista}
          onVista={setVista}
          onActualizar={() => void cargar()}
          onExportar={() => void exportar()}
        />
        <main className="p-6 space-y-6">
          {!cargado ? (
            <div className="space-y-4 py-8">
              <Skeleton className="h-8 w-64" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Skeleton className="h-44" />
                <Skeleton className="h-44" />
                <Skeleton className="h-44" />
                <Skeleton className="h-44" />
              </div>
            </div>
          ) : !puede("tablero") ? (
            <Card className="text-center py-10 text-muted-foreground">
              Tu rol no tiene acceso al tablero general (RF-04). Consulta los catalogos en el
              menu lateral.
            </Card>
          ) : cargando ? (
            <div className="space-y-4 py-8">
              <Skeleton className="h-8 w-48" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Skeleton className="h-44" />
                <Skeleton className="h-44" />
                <Skeleton className="h-44" />
                <Skeleton className="h-44" />
              </div>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                <div className="xl:col-span-2 space-y-4">
                  {vista === "general" ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {items.map((it) => (
                        <IndicatorCard
                          key={it.indicador.id}
                          indicador={it.indicador}
                          valor={it.valor}
                          meta={it.meta}
                          curso={cursoActual}
                          procesoNombre={it.procesoNombre}
                          procesoTipo={it.procesoTipo}
                        />
                      ))}
                    </div>
                  ) : (
                    porProceso.map(([nombre, lista]) => (
                      <div key={nombre}>
                        <h3 className="font-semibold text-cujae mb-2">{nombre}</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {lista.map((it) => (
                            <IndicatorCard
                              key={it.indicador.id}
                              indicador={it.indicador}
                              valor={it.valor}
                              meta={it.meta}
                              curso={cursoActual}
                              procesoNombre={it.procesoNombre}
                              procesoTipo={it.procesoTipo}
                            />
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                  {items.length === 0 && (
                    <div className="text-center text-muted-foreground py-10">Sin indicadores visibles</div>
                  )}
                </div>
                <div className="space-y-4">
                  <EstadoGeneral datos={distribucion} />
                  <GaugeEsenciales porcentaje={pctEsenciales} />
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
