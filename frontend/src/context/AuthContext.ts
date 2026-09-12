import { createContext } from "react";
import type { User } from "../types";

export type AuthContextType = {
  user: User | null;
  refreshUser: () => Promise<void>;
  logout: () => void;
};

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);
