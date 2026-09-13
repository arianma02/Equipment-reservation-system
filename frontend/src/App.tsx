import { Navigate, Route, Routes } from "react-router-dom";
import Header from "./components/Header";

import EquipmentPage from "./pages/EquipmentPage";
import EquipmentDetailPage from "./pages/EquipmentDetailPage";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";

import MyReservationsPage from "./pages/MyReservationsPage";

import ProtectedRoute from "./components/ProtectedRoute";

import AccountPage from "./pages/AccountPage";

import AdminRoute from "./components/AdminRoute";
import AdminPage from "./pages/AdminPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import AdminEquipmentPage from "./pages/AdminEquipmentPage";
import AdminCategoriesPage from "./pages/AdminCategoriesPage";
import AdminReservationsPage from "./pages/AdminReservationsPage";

function App() {
  return (
    <>
      <Header />

      <Routes>
        <Route path="/equipment" element={<EquipmentPage />} />
        <Route path="/" element={<Navigate to="/equipment" replace />} />
        <Route path="/equipment/:id" element={<EquipmentDetailPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/reservations/me"
          element={
            <ProtectedRoute>
              <MyReservationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/account"
          element={
            <ProtectedRoute>
              <AccountPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <AdminRoute>
              <AdminUsersPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/equipment"
          element={
            <AdminRoute>
              <AdminEquipmentPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/categories"
          element={
            <AdminRoute>
              <AdminCategoriesPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/reservations"
          element={
            <AdminRoute>
              <AdminReservationsPage />
            </AdminRoute>
          }
        />
      </Routes>
    </>
  );
}

export default App;
