import { Composition } from "remotion";
import { UgcReel, REEL_FPS, REEL_WIDTH, REEL_HEIGHT, REEL_FRAMES } from "./UgcReel";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="UgcReel"
        component={UgcReel}
        durationInFrames={REEL_FRAMES}
        fps={REEL_FPS}
        width={REEL_WIDTH}
        height={REEL_HEIGHT}
        defaultProps={{}}
      />
    </>
  );
};
