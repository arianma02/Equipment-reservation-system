import { apiFetch, SESSION_ENDED, SESSION_MESSAGE } from "../api";
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

  const response = await apiFetch(`${API_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401 || response.status === 403) {
    localStorage.removeItem("access_token");
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to load user");
  }

  return await response.json();
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [sessionMessage, setSessionMessage] = useState("");

  async function refreshUser() {
    try {
      const currentUser = await fetchCurrentUser();
      setUser(currentUser);
      if (currentUser) setSessionMessage("");
    } catch {
      return;
    }
  }

  function logout() {
    localStorage.removeItem("access_token");
    setSessionMessage("");
    setUser(null);
  }

  useEffect(() => {
    function sessionEnded() {
      setUser(null);
      setSessionMessage(SESSION_MESSAGE);
    }
    window.addEventListener(SESSION_ENDED, sessionEnded);
    return () => window.removeEventListener(SESSION_ENDED, sessionEnded);
  }, []);

  useEffect(() => {
    async function loadCurrentUser() {
      try {
        const currentUser = await fetchCurrentUser();
        setUser(currentUser);
      } catch {
        setUser(null);
      } finally {
        setAuthLoading(false);
      }
    }

    loadCurrentUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, authLoading, refreshUser, logout }}>
      {sessionMessage && <p role="alert">{sessionMessage}</p>}
      {children}
    </AuthContext.Provider>
  );
}
