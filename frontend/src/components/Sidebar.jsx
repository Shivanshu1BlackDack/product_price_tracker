import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  PackageCheck,
  ClipboardList,
} from "lucide-react";

import useProducts from "../hooks/useProducts";

function Sidebar() {
  const {
    products,
  } = useProducts();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">PT</div>

        <span>PriceTracker</span>
      </div>

      <div className="sidebar-content">
        <p className="sidebar-label">PLATFORM</p>

        <nav className="sidebar-nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `nav-item ${isActive ? "active" : ""}`
            }
          >
            <LayoutDashboard size={16} strokeWidth={1.8} />

            <span>Dashboard</span>
          </NavLink>

          <NavLink
            to="/products"
            className={({ isActive }) =>
              `nav-item ${isActive ? "active" : ""}`
            }
          >
            <PackageCheck size={16} strokeWidth={1.8} />

            <span>Tracked Products</span>

            <span className="nav-count">
              {products.length}
            </span>
          </NavLink>

          <NavLink
            to="/logs"
            className={({ isActive }) =>
              `nav-item ${isActive ? "active" : ""}`
            }
          >
            <ClipboardList size={16} strokeWidth={1.8} />

            <span>Scrape Logs</span>
          </NavLink>
        </nav>
      </div>

      <div className="sidebar-status">
        <span className="status-dot"></span>

        <div>
          <p className="status-title">Scraper: Active</p>

          <p className="status-subtitle">
            Worker nodes: 4/4
          </p>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
