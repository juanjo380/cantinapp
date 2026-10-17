import DarkModeIcon from "@mui/icons-material/DarkMode";
import DashboardIcon from "@mui/icons-material/SpaceDashboard";
import Drawer from "@mui/material/Drawer";
import IconButton from "@mui/material/IconButton";
import InsightsIcon from "@mui/icons-material/Insights";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import LightModeIcon from "@mui/icons-material/LightMode";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import LogoutIcon from "@mui/icons-material/Logout";
import MenuIcon from "@mui/icons-material/Menu";
import NotificationsActiveIcon from "@mui/icons-material/NotificationsActive";
import PointOfSaleIcon from "@mui/icons-material/PointOfSale";
import WarehouseIcon from "@mui/icons-material/Warehouse";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/context";
import { useColorMode } from "../../theme/color-mode";

const NAV = [
  { to: "/", label: "Dashboard", icon: DashboardIcon, end: true },
  { to: "/productos", label: "Productos", icon: Inventory2Icon },
  { to: "/inventario", label: "Inventario", icon: WarehouseIcon },
  { to: "/ventas", label: "Ventas", icon: PointOfSaleIcon },
  { to: "/analisis", label: "Análisis", icon: InsightsIcon },
  {
    to: "/reabastecimiento",
    label: "Reabastecimiento",
    icon: LocalShippingIcon,
  },
  { to: "/alertas", label: "Alertas", icon: NotificationsActiveIcon },
];

function Wordmark() {
  return (
    <div className="flex items-center gap-2.5 px-1">
      <span className="grid h-9 w-9 place-items-center rounded-md bg-brand-contrast text-lg font-black text-brand">
        C
      </span>
      <span className="text-xl font-extrabold tracking-tight text-brand-contrast">
        CantinAPP
      </span>
    </div>
  );
}

function NavList({ onNavigate }) {
  return (
    <nav className="flex flex-col gap-1" aria-label="Secciones">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `relative flex items-center gap-3 rounded-md px-3.5 py-2.5 text-sm font-medium transition-colors ${
              isActive
                ? "bg-brand-deep text-brand-contrast before:absolute before:inset-y-2 before:left-0 before:w-1 before:rounded-full before:bg-brand-contrast"
                : "text-brand-contrast/75 hover:bg-brand-contrast/10 hover:text-brand-contrast"
            }`
          }
        >
          <Icon fontSize="small" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

function RailFooter() {
  const { businessName, user, logout } = useAuth();
  const { active, setMode } = useColorMode();
  const navigate = useNavigate();

  async function onLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="mt-auto flex flex-col gap-4 border-t border-brand-contrast/20 pt-4">
      <div className="text-xs text-brand-contrast/70">
        <p className="font-mono tracking-stamp uppercase">Negocio</p>
        <p className="mt-1 truncate text-sm font-semibold text-brand-contrast">
          {businessName || user?.full_name || user?.email}
        </p>
      </div>
      <div className="flex items-center gap-1">
        <IconButton
          size="small"
          onClick={() => setMode(active === "dark" ? "light" : "dark")}
          aria-label={
            active === "dark" ? "Usar tema claro" : "Usar tema oscuro"
          }
          sx={{ color: "inherit" }}
        >
          {active === "dark" ? (
            <LightModeIcon fontSize="small" />
          ) : (
            <DarkModeIcon fontSize="small" />
          )}
        </IconButton>
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-2 rounded-md px-2.5 py-2 text-sm font-medium text-brand-contrast/90 transition-colors hover:bg-brand-contrast/10 hover:text-brand-contrast"
        >
          <LogoutIcon fontSize="small" />
          Cerrar sesión
        </button>
      </div>
    </div>
  );
}

export default function AppLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-svh bg-ground">
      <aside className="sticky top-0 hidden h-svh w-64 shrink-0 flex-col gap-8 bg-brand p-5 md:flex">
        <Wordmark />
        <NavList />
        <RailFooter />
      </aside>

      <header className="sticky top-0 z-20 flex items-center gap-2 bg-brand px-3 py-2.5 md:hidden">
        <IconButton
          onClick={() => setOpen(true)}
          aria-label="Abrir menú"
          sx={{ color: "inherit" }}
        >
          <MenuIcon />
        </IconButton>
        <Wordmark />
      </header>

      <Drawer
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{ paper: { className: "w-64 bg-brand p-5" } }}
      >
        <div className="mb-8">
          <Wordmark />
        </div>
        <NavList onNavigate={() => setOpen(false)} />
        <RailFooter />
      </Drawer>

      <main className="min-w-0 flex-1">
        <div className="mx-auto w-full max-w-6xl px-4 py-7 text-ink sm:px-6 lg:px-8 lg:py-9">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
