import { LineChart } from "lucide-react";
import { ModulePlaceholder } from "./ModulePlaceholder";

export function PredictionsPage() {
  return (
    <ModulePlaceholder
      title="Predictions"
      description="Modelos, previsões e séries temporais."
      icon={LineChart}
      capabilities={["Séries temporais e estatística", "Modelos preditivos explicáveis", "Distinção entre previsão, hipótese e fato"]}
    />
  );
}
