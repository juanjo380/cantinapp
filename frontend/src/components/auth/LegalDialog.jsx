import GavelIcon from '@mui/icons-material/GavelOutlined'
import FormDialog from '../ui/FormDialog'
import { Bottle, Star, Sun } from './AuthShell'

// shortcut: textos base redactados sin asesoría legal; un abogado debe revisarlos antes de operar con clientes reales.
const CONTACT = 'soporte@cantinapp.com'
const UPDATED = '1 de noviembre de 2026'

function Block({ title, children }) {
  return (
    <section className="flex flex-col gap-1.5">
      <h3 className="text-lg text-ink">{title}</h3>
      <div className="flex flex-col gap-1.5 text-sm text-ink-soft">{children}</div>
    </section>
  )
}

const LEGAL = {
  terms: {
    title: 'Términos y condiciones',
    body: (
      <>
        <Block title="1. Objeto">
          <p>
            CantinAPP es un servicio en línea para que pequeños negocios registren productos, ventas e inventario, y
            obtengan análisis, predicciones de demanda y recomendaciones de compra.
          </p>
        </Block>
        <Block title="2. Cuenta">
          <p>
            Quien crea la cuenta declara representar al negocio registrado y que los datos entregados son veraces.
            Eres responsable de guardar tu contraseña y de la actividad hecha con tu cuenta.
          </p>
        </Block>
        <Block title="3. Uso permitido">
          <p>
            No puedes usar el servicio para fines ilícitos, intentar acceder a datos de otros negocios ni afectar su
            funcionamiento. Podemos suspender cuentas que incumplan estas reglas.
          </p>
        </Block>
        <Block title="4. Tus datos">
          <p>
            Los datos de tu negocio son tuyos. Solo los usamos para prestarte el servicio, según la Política de
            privacidad. Cada negocio ve únicamente su propia información.
          </p>
        </Block>
        <Block title="5. Predicciones">
          <p>
            Las predicciones y recomendaciones son estimaciones calculadas con tu historial. Son una ayuda para
            decidir, no una garantía de ventas: la decisión final de compra es tuya.
          </p>
        </Block>
        <Block title="6. Disponibilidad">
          <p>
            Hacemos lo razonable para que el servicio esté disponible, pero puede haber pausas por mantenimiento o
            fallas de terceros (hosting, base de datos).
          </p>
        </Block>
        <Block title="7. Cambios y contacto">
          <p>
            Podemos actualizar estos términos y te avisaremos en la aplicación. Ley aplicable: República de
            Colombia. Contacto: {CONTACT}.
          </p>
        </Block>
      </>
    ),
  },
  privacy: {
    title: 'Política de privacidad y cookies',
    body: (
      <>
        <Block title="Responsable">
          <p>
            CantinAPP trata tus datos personales conforme a la Ley 1581 de 2012 y el Decreto 1377 de 2013
            (compilado en el Decreto 1074 de 2015). Contacto: {CONTACT}.
          </p>
        </Block>
        <Block title="Qué datos tratamos">
          <p>
            Nombre del negocio, tu nombre (opcional), correo y contraseña (guardada cifrada, nunca en texto plano), y
            la información que registras: productos, ventas, inventario y proveedores.
          </p>
        </Block>
        <Block title="Para qué">
          <p>
            Crear y proteger tu cuenta, prestarte las funciones del servicio (inventario, análisis, predicciones y
            alertas) y contactarte sobre tu cuenta. No vendemos tus datos.
          </p>
        </Block>
        <Block title="Tus derechos">
          <p>
            Puedes conocer, actualizar, rectificar y pedir la supresión de tus datos, revocar tu autorización y
            presentar quejas ante la Superintendencia de Industria y Comercio. Escríbenos a {CONTACT}.
          </p>
        </Block>
        <Block title="Seguridad y conservación">
          <p>
            Los datos viajan cifrados (HTTPS) y cada negocio está aislado del resto. Los conservamos mientras tu cuenta
            esté activa o la ley lo exija.
          </p>
        </Block>
        <Block title="Cookies y almacenamiento local">
          <p>
            CantinAPP no usa cookies de publicidad ni de analítica. Solo guarda en tu navegador (almacenamiento local)
            lo necesario para funcionar:
          </p>
          <ul className="list-disc pl-5">
            <li>tu sesión (token de acceso) y los datos básicos de tu usuario;</li>
            <li>tu preferencia de tema claro u oscuro.</li>
          </ul>
          <p>
            Las tipografías se cargan desde Google Fonts, por lo que tu navegador se conecta a Google y este recibe tu
            dirección IP. Al cerrar sesión se borra tu sesión; también puedes borrar los datos del sitio desde la
            configuración de tu navegador (tendrás que volver a iniciar sesión).
          </p>
        </Block>
      </>
    ),
  },
  ml: {
    title: 'Uso anónimo de datos para predicciones',
    body: (
      <>
        <Block title="Qué autorizas">
          <p>
            Que usemos el historial de ventas e inventario de tu negocio, de forma anónima y agregada, para entrenar y
            mejorar los modelos de predicción de demanda de CantinAPP.
          </p>
        </Block>
        <Block title="Cómo se anonimiza">
          <p>
            Antes de usarlos quitamos el nombre del negocio, los usuarios, los correos y cualquier dato que permita
            identificarte. Los modelos aprenden patrones (por ejemplo, temporadas), no datos de un negocio concreto.
          </p>
        </Block>
        <Block title="Es opcional">
          <p>
            Tus propias predicciones funcionan igual aunque no lo autorices. Puedes revocar esta autorización cuando
            quieras escribiendo a {CONTACT}.
          </p>
        </Block>
      </>
    ),
  },
}

// Modal legal con el mismo estilo de boceto del acceso: figuras en las esquinas.
export default function LegalDialog({ doc, onClose, onAccept }) {
  const { title, body } = LEGAL[doc]
  return (
    <FormDialog
      title={title}
      icon={<GavelIcon />}
      maxWidth="sm"
      onClose={onClose}
      onSubmit={onAccept}
      submitLabel="Aceptar"
      cancelLabel="Cerrar"
      decor={
        <>
          <Bottle className="pointer-events-none absolute bottom-3 left-4 h-14 w-10" />
          <Sun className="pointer-events-none absolute bottom-3 left-14 h-14 w-14" />
          <Star className="pointer-events-none absolute bottom-10 left-28 h-6 w-6" />
        </>
      }
    >
      <p className="text-stamp font-bold tracking-stamp uppercase text-ink-soft">Última actualización: {UPDATED}</p>
      {body}
    </FormDialog>
  )
}
