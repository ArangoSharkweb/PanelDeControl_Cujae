import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export interface Perfil {
  id: string;
  username: string;
  email: string | null;
  rol: string;
  auth_type: string;
  alcance_tipo: string | null;
}

interface AuthState {
  token: string | null;
  perfil: Perfil | null;
  hidratado: boolean;
  setSesion: (token: string, perfil: Perfil) => void;
  cerrarSesion: () => void;
  marcarHidratado: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      perfil: null,
      hidratado: false,
      setSesion: (token, perfil) => set({ token, perfil }),
      cerrarSesion: () => set({ token: null, perfil: null }),
      marcarHidratado: () => set({ hidratado: true }),
    }),
    {
      name: "cujae-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ token: s.token, perfil: s.perfil }),
      onRehydrateStorage: () => (state) => {
        state?.marcarHidratado();
      },
    }
  )
);
