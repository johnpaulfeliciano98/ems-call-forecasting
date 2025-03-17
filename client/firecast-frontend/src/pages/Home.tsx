import React from "react";
import Heatmap from "../components/Heatmap.component";

import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";

const Home: React.FC = () => {
  return (
    <section
      style={{
        width: "100vw",
      }}
    >
      <main>
        <Heatmap />
      </main>
    </section>
  );
};

export default Home;
