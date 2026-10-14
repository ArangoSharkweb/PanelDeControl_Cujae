"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puede } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

interface Usuario {
  id: string;
  username: string;
  email: string | null;
  rol: string;
  auth_type: string;
  alcance_tipo: string;
  alcance_id: string | null;
  activo: boolean;
  fecha_creacion: string;
}

const ROLES = ["administrador", "alta_direccion", "directivo", "jefe_proceso", "auditor"];
const ALCANCES = ["institucional", "unidad", "proceso"];

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [nuevo, setNuevo] = useState({
    username: "",
    password: "",
    email: "",
    rol: "directivo",
    auth_type: "local",
    alcance_tipo: "institucional",
  });
  const [mostrarForm, setMostrarForm] = useState(false);
  const { cargado } = usePerfil();

  const cargar = async () => {
    setUsuarios(await api<Usuario[]>("/usuarios"));
  };

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    if (!puede("usuarios")) return;
    void cargar().catch(() => setMensaje("No se pudo cargar la lista de usuarios"));
  }, []);

  const guardarFila = async (u: Usuario) => {
    try {
      await api(`/usuarios/${u.id}`, {
        method: "PUT",
        body: JSON.stringify({
          username: u.username,
          email: u.email,
          rol: u.rol,
          auth_type: u.auth_type,
          alcance_tipo: u.alcance_tipo,
          alcance_id: u.alcance_id,
          activo: u.activo,
        }),
      });
      setMensaje(`Usuario "${u.username}" actualizado`);
      await cargar();
    } catch (e) {
      setMensaje(e instanceof Error ? e.message : "Error al actualizar");
    }
  };

  const crearUsuario = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api("/usuarios", {
        method: "POST",
        body: JSON.stringify({
          username: nuevo.username,
          password: nuevo.password || null,
          email: nuevo.email || null,
          rol: nuevo.rol,
          auth_type: nuevo.auth_type,
          alcance_tipo: nuevo.alcance_tipo,
          activo: true,
        }),
      });
      setMensaje(`Usuario "${nuevo.username}" creado`);
      setMostrarForm(false);
      setNuevo({ username: "", password: "", email: "", rol: "directivo", auth_type: "local", alcance_tipo: "institucional" });
      await cargar();
    } catch (err) {
      setMensaje(err instanceof Error ? err.message : "Error al crear usuario");
    }
  };

  const resetPassword = async (u: Usuario) => {
    const nueva = window.prompt(`Nueva contraseña para "${u.username}" (minimo 8 caracteres):`);
    if (!nueva) return;
    if (nueva.length < 8) {
      setMensaje("La contraseña debe tener al menos 8 caracteres");
      return;
    }
    try {
      await api(`/usuarios/${u.id}/password`, {
        method: "PUT",
        body: JSON.stringify({ nueva_password: nueva }),
      });
      setMensaje(`Contraseña de "${u.username}" restablecida`);
    } catch (err) {
      setMensaje(err instanceof Error ? err.message : "Error al restablecer");
    }
  };

  if (!cargado) return null;

  if (!puede("usuarios")) {
    return (
      <div className="min-h-screen">
        <Sidebar />
        <div className="ml-64 p-6">
          <Card className="text-center py-10 text-muted-foreground">
            Tu rol no tiene acceso a la administracion de usuarios (RF-04).
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-64 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">Administracion de usuarios</h1>
          <Button onClick={() => setMostrarForm((v) => !v)}>
            {mostrarForm ? "Cancelar" : "+ Nuevo usuario"}
          </Button>
        </div>

        {mensaje && (
          <div className="bg-accent text-accent-foreground text-sm rounded-lg px-3 py-2">{mensaje}</div>
        )}

        {mostrarForm && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Nuevo usuario</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={crearUsuario} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <Input
                  placeholder="Usuario *"
                  value={nuevo.username}
                  onChange={(e) => setNuevo({ ...nuevo, username: e.target.value })}
                  required
                />
                <Input
                  type="password"
                  placeholder="Contrasena *"
                  value={nuevo.password}
                  onChange={(e) => setNuevo({ ...nuevo, password: e.target.value })}
                  required={nuevo.auth_type === "local"}
                  minLength={8}
                />
                <Input
                  type="email"
                  placeholder="Email (opcional)"
                  value={nuevo.email}
                  onChange={(e) => setNuevo({ ...nuevo, email: e.target.value })}
                />
                <Select value={nuevo.rol} onValueChange={(v) => setNuevo({ ...nuevo, rol: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Rol" />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((r) => (
                      <SelectItem key={r} value={r}>
                        {r}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={nuevo.auth_type} onValueChange={(v) => setNuevo({ ...nuevo, auth_type: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Autenticacion" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="local">Local</SelectItem>
                    <SelectItem value="ldap">LDAP</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={nuevo.alcance_tipo} onValueChange={(v) => setNuevo({ ...nuevo, alcance_tipo: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Alcance" />
                  </SelectTrigger>
                  <SelectContent>
                    {ALCANCES.map((a) => (
                      <SelectItem key={a} value={a}>
                        {a}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button type="submit" className="md:col-span-2">
                  Crear usuario
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>USUARIO</TableHead>
                  <TableHead>EMAIL</TableHead>
                  <TableHead>ROL</TableHead>
                  <TableHead>ALCANCE</TableHead>
                  <TableHead>AUTENTICACION</TableHead>
                  <TableHead>ACTIVO</TableHead>
                  <TableHead>ACCIONES</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usuarios.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-semibold text-cujae">{u.username}</TableCell>
                    <TableCell>{u.email ?? "-"}</TableCell>
                    <TableCell>
                      <Select
                        value={u.rol}
                        onValueChange={(v) =>
                          setUsuarios((prev) => prev.map((x) => (x.id === u.id ? { ...x, rol: v } : x)))
                        }
                      >
                        <SelectTrigger className="h-8 w-40">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {ROLES.map((r) => (
                            <SelectItem key={r} value={r}>
                              {r}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>{u.alcance_tipo}</TableCell>
                    <TableCell>
                      <Badge variant={u.auth_type === "ldap" ? "info" : "secondary"}>{u.auth_type}</Badge>
                    </TableCell>
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={u.activo}
                        onChange={(e) =>
                          setUsuarios((prev) =>
                            prev.map((x) => (x.id === u.id ? { ...x, activo: e.target.checked } : x))
                          )
                        }
                      />
                    </TableCell>
                    <TableCell className="space-x-2 whitespace-nowrap">
                      <Button variant="link" size="sm" className="h-auto p-0" onClick={() => void guardarFila(u)}>
                        Guardar
                      </Button>
                      <Button
                        variant="link"
                        size="sm"
                        className="h-auto p-0 text-amber-600"
                        onClick={() => void resetPassword(u)}
                      >
                        Reset clave
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {usuarios.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                      Sin usuarios
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
