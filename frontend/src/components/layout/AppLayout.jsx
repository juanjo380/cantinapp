import DarkModeIcon from "@mui/icons-material/DarkModeOutlined";
import DashboardIcon from "@mui/icons-material/SpaceDashboardOutlined";
import Drawer from "@mui/material/Drawer";
import IconButton from "@mui/material/IconButton";
import InsightsIcon from "@mui/icons-material/InsightsOutlined";
import Inventory2Icon from "@mui/icons-material/Inventory2Outlined";
import LightModeIcon from "@mui/icons-material/LightModeOutlined";
import LocalShippingIcon from "@mui/icons-material/LocalShippingOutlined";
import LogoutIcon from "@mui/icons-material/Logout";
import MenuIcon from "@mui/icons-material/Menu";
import NotificationsActiveIcon from "@mui/icons-material/NotificationsNoneOutlined";
import PointOfSaleIcon from "@mui/icons-material/ShoppingCartOutlined";
import WarehouseIcon from "@mui/icons-material/ArchiveOutlined";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/context";
import { useColorMode } from "../../theme/color-mode";
import Logo from "../ui/Logo";

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

function NavList({ onNavigate }) {
  return (
    <nav className="flex flex-col gap-2" aria-label="Secciones">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-2.5 text-[0.9375rem] transition-colors ${
              isActive
                ? "surface border-edge bg-brand-tint font-bold text-brand-ink"
                : "border-2 border-transparent font-medium text-ink-soft hover:text-ink"
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
    <div className="mt-auto border-t-2 border-dashed border-line pt-6">
      <p className="text-stamp font-bold tracking-stamp uppercase text-ink-soft">Negocio</p>
      <p className="mt-1 mb-4 truncate text-sm font-bold text-ink">
        {businessName || user?.full_name || user?.email}
      </p>
      <div className="flex items-center justify-between gap-2">
        <IconButton
          size="small"
          onClick={() => setMode(active === "dark" ? "light" : "dark")}
          aria-label={active === "dark" ? "Usar tema claro" : "Usar tema oscuro"}
          className="surface"
          sx={{
            borderRadius: "var(--radius-sketch)",
            background: "transparent",
            "&:hover": { backgroundColor: "var(--ink)", color: "var(--ground)", borderRadius: "var(--radius-sketch-alt)" },
          }}
        >
          {active === "dark" ? <LightModeIcon fontSize="small" /> : <DarkModeIcon fontSize="small" />}
        </IconButton>
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-2 text-sm font-semibold text-ink-soft transition-colors hover:text-brand-ink"
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
      <aside className="sticky top-0 hidden h-svh w-64 shrink-0 flex-col gap-10 overflow-y-auto border-r-2 border-edge p-6 md:flex">
        <Logo />
        <NavList />
        <RailFooter />
      </aside>

      <header className="sticky top-0 z-20 flex items-center gap-2 border-b-2 border-edge bg-ground px-3 py-2.5 md:hidden">
        <IconButton onClick={() => setOpen(true)} aria-label="Abrir menú">
          <MenuIcon />
        </IconButton>
        <Logo size="sm" />
      </header>

      <Drawer
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{ paper: { className: "flex w-64 flex-col gap-10 p-6" } }}
      >
        <Logo />
        <NavList onNavigate={() => setOpen(false)} />
        <RailFooter />
      </Drawer>

      <main className="min-w-0 flex-1">
        <div className="mx-auto w-full max-w-6xl px-4 py-7 text-ink sm:px-6 md:px-10 md:py-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
