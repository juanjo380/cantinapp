import DarkModeIcon from "@mui/icons-material/DarkModeOutlined";
import DashboardIcon from "@mui/icons-material/SpaceDashboardOutlined";
import Button from "@mui/material/Button";
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
import StorefrontIcon from "@mui/icons-material/StorefrontOutlined";
import UnfoldMoreIcon from "@mui/icons-material/UnfoldMore";
import WarehouseIcon from "@mui/icons-material/ArchiveOutlined";
import { Suspense, useCallback, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/context";
import { useColorMode } from "../../theme/color-mode";
import { ROLE_LABELS } from "../../utils/format";
import Logo from "../ui/Logo";
import { Empty, PageSkeleton } from "../ui/States";
import BusinessDialog from "./BusinessDialog";
import OnboardingDialog from "./OnboardingDialog";

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

// Negocio activo + acceso al selector (cambiar o crear negocio).
function BusinessSwitcher({ onOpen, compact = false }) {
  const { session, businessName } = useAuth();
  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label={`Negocio activo: ${businessName || "ninguno"}. Cambiar de negocio`}
      className={`surface-inset flex min-w-0 cursor-pointer items-center gap-2 text-left transition-colors hover:bg-brand-tint ${
        compact ? "max-w-48 px-2.5 py-2" : "w-full px-3 py-2.5"
      }`}
    >
      <StorefrontIcon fontSize="small" className="shrink-0 text-brand-ink" />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-bold text-ink">{businessName || "Elige un negocio"}</span>
        {!compact && session?.role && (
          <span className="block text-xs text-ink-soft">{ROLE_LABELS[session.role]}</span>
        )}
      </span>
      <UnfoldMoreIcon fontSize="small" className="shrink-0 text-ink-soft" />
    </button>
  );
}

function RailFooter({ profileRef, onNavigate }) {
  const { session, businessName, user, logout } = useAuth();
  const { active, setMode } = useColorMode();
  const navigate = useNavigate();
  const complete = Boolean(session?.profile_completed);

  async function onLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="mt-auto border-t-2 border-dashed border-line pt-6">
      {/* Al completar el perfil, «Negocio» se reemplaza por el nombre del negocio. */}
      <NavLink
        ref={profileRef}
        to="/perfil"
        onClick={onNavigate}
        className="-mx-2 mb-4 block px-2 py-1.5 transition-colors hover:bg-brand-tint [border-radius:var(--radius-sketch-sm)]"
      >
        <p
          className={`truncate ${
            complete
              ? "font-display text-lg font-bold text-ink"
              : "text-stamp font-bold tracking-stamp uppercase text-ink-soft"
          }`}
        >
          {complete ? businessName : "Negocio"}
        </p>
        <p className={`mt-0.5 truncate text-sm ${complete ? "text-ink-soft" : "font-bold text-brand-ink"}`}>
          {complete ? user?.full_name || user?.email : "Completa tu perfil →"}
        </p>
      </NavLink>
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
  const { session, needsPick, setNeedsPick } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [picking, setPicking] = useState(false);
  const profileRef = useRef(null);
  const menuRef = useRef(null);
  const hasBusiness = Boolean(session?.business_id);
  const onboarding = Boolean(location.state?.onboarding) && hasBusiness;

  // En escritorio la flecha apunta al bloque «Negocio»; en móvil (barra oculta), al botón de menú.
  const getTarget = useCallback(
    () => (profileRef.current?.offsetParent ? profileRef.current : menuRef.current),
    [],
  );
  const closeOnboarding = () => navigate(location.pathname, { replace: true, state: null });
  const closePicker = () => {
    setPicking(false);
    setNeedsPick(false);
  };

  return (
    // Columna en móvil (header arriba, contenido abajo); fila desde md (barra lateral + contenido).
    <div className="flex min-h-svh flex-col bg-ground md:flex-row">
      <aside className="sticky top-0 hidden h-svh w-64 shrink-0 flex-col gap-8 overflow-y-auto border-r-2 border-edge p-6 md:flex">
        <Logo />
        <BusinessSwitcher onOpen={() => setPicking(true)} />
        <NavList />
        <RailFooter profileRef={profileRef} />
      </aside>

      <header className="sticky top-0 z-20 flex items-center gap-2 border-b-2 border-edge bg-ground px-3 py-2.5 md:hidden">
        <IconButton ref={menuRef} onClick={() => setOpen(true)} aria-label="Abrir menú">
          <MenuIcon />
        </IconButton>
        <Logo size="sm" />
        <div className="ml-auto flex min-w-0 flex-1 justify-end">
          <BusinessSwitcher compact onOpen={() => setPicking(true)} />
        </div>
      </header>

      <Drawer
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{ paper: { className: "flex w-64 flex-col gap-8 p-6" } }}
      >
        <Logo />
        <NavList onNavigate={() => setOpen(false)} />
        <RailFooter onNavigate={() => setOpen(false)} />
      </Drawer>

      <main className="min-w-0 flex-1">
        <div className="mx-auto w-full max-w-6xl px-4 py-7 text-ink sm:px-6 md:px-10 md:py-10">
          {hasBusiness ? (
            // Suspense aquí (no en App): al cargar el código de una página la barra lateral sigue visible.
            <Suspense fallback={<PageSkeleton />}>
              {/* La key remonta las páginas al cambiar de negocio: ningún dato del anterior queda en pantalla. */}
              <Outlet key={session.business_id} />
            </Suspense>
          ) : (
            <Empty
              icon={<StorefrontIcon />}
              title="No tienes un negocio activo"
              action={
                <Button variant="contained" onClick={() => setPicking(true)}>
                  {session?.businesses?.length ? "Elegir negocio" : "Crear mi negocio"}
                </Button>
              }
            >
              Elige uno de tus negocios o crea uno nuevo para empezar.
            </Empty>
          )}
        </div>
      </main>

      {(picking || needsPick) && <BusinessDialog onClose={closePicker} />}
      {onboarding && !picking && (
        <OnboardingDialog
          getTarget={getTarget}
          onClose={closeOnboarding}
          onStart={() => navigate("/perfil?tab=negocio", { replace: true, state: null })}
        />
      )}
    </div>
  );
}
