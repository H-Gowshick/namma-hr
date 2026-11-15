/**
 * Reveal streamed text gradually so the UI always feels like typing,
 * even when the network delivers large chunks in one read.
 */
export type StreamRevealController = {
  push: (fullText: string) => void;
  finish: () => Promise<void>;
  cancel: () => void;
};

type StreamRevealOptions = {
  onUpdate: (visibleText: string) => void;
  /** Characters revealed per tick while catching up. */
  charsPerTick?: number;
  /** Delay between reveal ticks in ms. */
  tickMs?: number;
};

export function createStreamReveal(
  options: StreamRevealOptions,
): StreamRevealController {
  const charsPerTick = options.charsPerTick ?? 3;
  const tickMs = options.tickMs ?? 18;

  let target = "";
  let visible = "";
  let timer: ReturnType<typeof setInterval> | null = null;
  let finishResolver: (() => void) | null = null;
  let cancelled = false;

  function clearTimer() {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  }

  function settleIfCaughtUp() {
    if (visible.length >= target.length && finishResolver) {
      const resolve = finishResolver;
      finishResolver = null;
      clearTimer();
      resolve();
    }
  }

  function tick() {
    if (cancelled) {
      return;
    }

    if (visible.length >= target.length) {
      settleIfCaughtUp();
      return;
    }

    const nextLength = Math.min(target.length, visible.length + charsPerTick);
    visible = target.slice(0, nextLength);
    options.onUpdate(visible);
    settleIfCaughtUp();
  }

  function ensureTimer() {
    if (timer !== null || cancelled) {
      return;
    }

    timer = setInterval(tick, tickMs);
  }

  return {
    push(fullText: string) {
      if (cancelled) {
        return;
      }

      // Streamed answers only grow; ignore any non-monotonic glitch.
      if (fullText.length < target.length && !fullText.startsWith(visible)) {
        target = fullText;
        visible = fullText;
        options.onUpdate(visible);
        return;
      }

      target = fullText.length >= target.length ? fullText : target;
      ensureTimer();
      tick();
    },

    finish() {
      if (cancelled) {
        return Promise.resolve();
      }

      if (visible.length >= target.length) {
        clearTimer();
        options.onUpdate(target);
        return Promise.resolve();
      }

      ensureTimer();

      return new Promise<void>((resolve) => {
        finishResolver = resolve;
      });
    },

    cancel() {
      cancelled = true;
      clearTimer();
      if (finishResolver) {
        finishResolver();
        finishResolver = null;
      }
    },
  };
}
