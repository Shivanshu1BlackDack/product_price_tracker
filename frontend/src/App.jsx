import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import DashboardLayout from "./layouts/DashboardLayout";

import Dashboard from "./pages/Dashboard";
import TrackedProducts from "./pages/TrackedProducts";
import ProductDetails from "./pages/ProductDetails";
import ScrapeLogs from "./pages/ScrapeLogs";
import NotFound from "./pages/NotFound";


function App() {
  return (
    <BrowserRouter>

      <Routes>

        <Route
          element={
            <DashboardLayout />
          }
        >

          <Route
            path="/"
            element={
              <Dashboard />
            }
          />

          <Route
            path="/products"
            element={
              <TrackedProducts />
            }
          />

          <Route
            path="/logs"
            element={
              <ScrapeLogs />
            }
          />

          <Route
            path="/product/:id"
            element={
              <ProductDetails />
            }
          />

        </Route>


        <Route
          path="*"
          element={
            <NotFound />
          }
        />

      </Routes>

    </BrowserRouter>
  );
}


export default App;