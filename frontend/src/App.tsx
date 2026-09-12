import { Navigate, Route, Routes } from "react-router-dom";
import Header from "./components/Header";
import EquipmentPage from "./pages/EquipmentPage";
import EquipmentDetailPage from "./pages/EquipmentDetailPage";

function App() {
  return (
    <>
      <Header />

      <Routes>
        <Route path="/equipment" element={<EquipmentPage />} />
        <Route path="/" element={<Navigate to="/equipment" replace />} />
        <Route path="/equipment/:id" element={<EquipmentDetailPage />} />
      </Routes>
    </>
  );
}

export default App;
