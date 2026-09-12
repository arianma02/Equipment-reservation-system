import { Navigate, Route, Routes } from "react-router-dom";
import Header from "./components/Header";
import EquipmentPage from "./pages/EquipmentPage";
import EquipmentDetailPage from "./pages/EquipmentDetailPage";
import LoginPage from "./pages/LoginPage";

function App() {
  return (
    <>
      <Header />

      <Routes>
        <Route path="/equipment" element={<EquipmentPage />} />
        <Route path="/" element={<Navigate to="/equipment" replace />} />
        <Route path="/equipment/:id" element={<EquipmentDetailPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </>
  );
}

export default App;
