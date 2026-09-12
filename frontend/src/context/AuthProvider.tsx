import { useEffect, useState, type ReactNode } from "react";
import { API_URL } from "../config";
import type { User } from "../types";
import { AuthContext } from "./AuthContext";

type AuthProviderProps = {
  children: ReactNode;
};

async function fetchCurrentUser(): Promise<User | null> {
  const token = localStorage.getItem("access_token");

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${API_URL}/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to load user");
    }

    return await response.json();
  } catch {
    localStorage.removeItem("access_token");
    return null;
  }
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  async function refreshUser() {
    const currentUser = await fetchCurrentUser();
    setUser(currentUser);
  }

  function logout() {
    localStorage.removeItem("access_token");
    setUser(null);
  }

  useEffect(() => {
    async function loadCurrentUser() {
      const currentUser = await fetchCurrentUser();
      setUser(currentUser);
      setAuthLoading(false);
    }

    loadCurrentUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, authLoading, refreshUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
