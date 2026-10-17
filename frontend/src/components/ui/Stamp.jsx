import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import ErrorOutlinedIcon from "@mui/icons-material/ErrorOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { formatDateTime } from "../../utils/format";

const TONES = {
  ok: "border-ok bg-ok-tint text-ok",
  warn: "border-warn bg-warn-tint text-warn",
  crit: "border-crit bg-crit-tint text-crit",
  neutral: "border-line bg-panel text-ink-soft",
};

const iconStyle = { fontSize: "1.05rem" };

export function Stamp({ tone = "neutral", icon, children }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-stamp tracking-stamp uppercase ${TONES[tone]}`}
    >
      {icon}
      {children}
    </span>
  );
}

const STATUS = {
  NORMAL: {
    tone: "ok",
    label: "Normal",
    icon: <CheckCircleOutlinedIcon style={iconStyle} />,
  },
  BAJO: {
    tone: "warn",
    label: "Bajo",
    icon: <WarningAmberIcon style={iconStyle} />,
  },
  AGOTADO: {
    tone: "crit",
    label: "Agotado",
    icon: <ErrorOutlinedIcon style={iconStyle} />,
  },
};

export function StatusStamp({ status }) {
  const s = STATUS[status] || {
    tone: "neutral",
    label: status,
    icon: <InfoOutlinedIcon style={iconStyle} />,
  };
  return (
    <Stamp tone={s.tone} icon={s.icon}>
      {s.label}
    </Stamp>
  );
}

const URGENCY = {
  BAJO: { tone: "ok", label: "Urgencia baja" },
  MEDIO: { tone: "warn", label: "Urgencia media" },
  ALTO: { tone: "crit", label: "Urgencia alta" },
};

export function UrgencyStamp({ urgency }) {
  const u = URGENCY[urgency] || { tone: "neutral", label: urgency };
  return <Stamp tone={u.tone}>{u.label}</Stamp>;
}

// Sello de procedencia: todo lo que genera el Sistema muestra cuándo y sobre qué base.
export function ProvenanceStamp({ date, base }) {
  return (
    <Stamp tone="neutral" icon={<InfoOutlinedIcon style={iconStyle} />}>
      Generado {formatDateTime(date)}
      {base ? ` · ${base}` : ""}
    </Stamp>
  );
}
