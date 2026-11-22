/* Charge le maillot 3D seulement sur ordinateur, après le reste de la page.
   Sur téléphone (ou en mode économie de données), le carrousel photo suffit : pas de 3D téléchargée. */
const desktop = matchMedia("(min-width: 861px) and (pointer: fine)").matches;
const saveData = navigator.connection && navigator.connection.saveData;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

if (desktop && !saveData && !reduce) {
  const go = () => import("./jersey3d.js");
  const later = () => ("requestIdleCallback" in window ? requestIdleCallback(go, { timeout: 2500 }) : setTimeout(go, 800));
  if (document.readyState === "complete") later();
  else addEventListener("load", later, { once: true });
}
