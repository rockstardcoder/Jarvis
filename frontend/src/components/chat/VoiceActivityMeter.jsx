import { useEffect, useRef, useState } from "react";

const BAR_COUNT = 18;

function fallbackLevels(tick) {
  return Array.from({ length: BAR_COUNT }, (_, index) => {
    const wave = Math.sin(tick / 140 + index * 0.75);
    const wave2 = Math.sin(tick / 210 + index * 0.35);
    return 18 + Math.abs(wave + wave2) * 26;
  });
}

export default function VoiceActivityMeter({ active }) {
  const [levels, setLevels] = useState(() => Array(BAR_COUNT).fill(14));
  const rafRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const stopAudio = () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
    };

    if (!active) {
      stopAudio();
      setLevels(Array(BAR_COUNT).fill(10));
      return stopAudio;
    }

    async function startMeter() {
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error("Web audio mic unavailable");
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: false,
        });

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;

        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        const audioContext = new AudioContextClass();
        audioContextRef.current = audioContext;

        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 64;
        analyser.smoothingTimeConstant = 0.72;

        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);

        const data = new Uint8Array(analyser.frequencyBinCount);

        const loop = () => {
          analyser.getByteFrequencyData(data);

          const nextLevels = Array.from({ length: BAR_COUNT }, (_, index) => {
            const dataIndex = Math.min(data.length - 1, index + 2);
            const raw = data[dataIndex] || 0;
            return Math.max(8, Math.min(58, 8 + raw / 4));
          });

          setLevels(nextLevels);
          rafRef.current = requestAnimationFrame(loop);
        };

        loop();
      } catch {
        const fallbackLoop = (time) => {
          setLevels(fallbackLevels(time));
          rafRef.current = requestAnimationFrame(fallbackLoop);
        };

        rafRef.current = requestAnimationFrame(fallbackLoop);
      }
    }

    startMeter();

    return () => {
      cancelled = true;
      stopAudio();
    };
  }, [active]);

  return (
    <div className="flex h-10 items-center justify-center gap-1.5 rounded-full border border-primary-container/20 bg-background/60 px-4 shadow-glow-soft backdrop-blur-xl">
      {levels.map((height, index) => (
        <span
          key={index}
          className="w-1 rounded-full bg-gradient-to-t from-primary-green via-primary-container to-primary-blue transition-[height,opacity] duration-100"
          style={{
            height: `${height}px`,
            opacity: active ? 0.95 : 0.35,
          }}
        />
      ))}
    </div>
  );
}