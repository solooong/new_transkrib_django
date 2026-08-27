/* Лёгкие canvas-графики без внешних зависимостей: полукруглые датчики и линейный chart. */

function colorFor(value) {
  if (value < 55) return "#41d393";
  if (value < 80) return "#f2a33c";
  return "#f26d64";
}

export class Gauge {
  /**
   * @param {HTMLElement} root — блок .gauge с <canvas>, .gauge-num внутри
   */
  constructor(root) {
    this.canvas = root.querySelector("canvas");
    this.numEl = root.querySelector(".gauge-num");
    this.ctx = this.canvas.getContext("2d");
    this.value = null;
  }

  set(value) {
    this.value = value;
    if (value === null || value === undefined) {
      this.numEl.textContent = "н/д";
      this.numEl.style.color = "#7c8aa5";
      this._draw(null);
      return;
    }
    const v = Math.max(0, Math.min(100, value));
    this.numEl.textContent = Math.round(v) + "%";
    this.numEl.style.color = colorFor(v);
    this._draw(v);
  }

  _draw(value) {
    const canvas = this.canvas;
    const dpr = window.devicePixelRatio || 1;
    const w = 150;
    const h = 84;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = this.ctx;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h - 8;
    const r = 56;
    const start = Math.PI;
    const end = 2 * Math.PI;

    // подложка
    ctx.lineWidth = 9;
    ctx.lineCap = "round";
    ctx.strokeStyle = "rgba(120,140,175,0.16)";
    ctx.beginPath();
    ctx.arc(cx, cy, r, start, end);
    ctx.stroke();

    if (value !== null) {
      const color = colorFor(value);
      ctx.strokeStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.arc(cx, cy, r, start, start + (Math.PI * value) / 100);
      ctx.stroke();
      ctx.shadowBlur = 0;
    }
  }
}

export class LineChart {
  /**
   * @param {HTMLCanvasElement} canvas
   * @param {{series: string[], colors: Object<string,string>}} opts
   */
  constructor(canvas, opts) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.series = opts.series;
    this.colors = opts.colors;
    this.points = [];

    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(() => this.draw(this.points)).observe(canvas.parentElement);
    }
  }

  draw(points) {
    this.points = points;
    const canvas = this.canvas;
    const rect = canvas.parentElement.getBoundingClientRect();
    const w = Math.max(100, rect.width);
    const h = Math.max(60, rect.height);
    const dpr = window.devicePixelRatio || 1;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = this.ctx;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const padL = 34;
    const padR = 10;
    const padT = 12;
    const padB = 22;
    const iw = w - padL - padR;
    const ih = h - padT - padB;

    // сетка и подписи 0..100%
    ctx.font = "9.5px 'JetBrains Mono', monospace";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    [0, 25, 50, 75, 100].forEach((v) => {
      const y = padT + ih - (v / 100) * ih;
      ctx.strokeStyle = "rgba(120,140,175,0.13)";
      ctx.setLineDash([3, 5]);
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(w - padR, y);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#7c8aa5";
      ctx.fillText(String(v), padL - 7, y);
    });

    const data = points.slice(-180);
    if (data.length < 2) return;

    const xAt = (i) => padL + (i / (data.length - 1)) * iw;
    const yAt = (v) => padT + ih - (Math.max(0, Math.min(100, v)) / 100) * ih;

    // подписи времени (первая/средняя/последняя точки)
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = "#7c8aa5";
    const fmt = (t) => {
      const d = new Date(t);
      return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    };
    ctx.fillText(fmt(data[0].t), padL + 14, h - padB + 7);
    ctx.fillText(fmt(data[Math.floor(data.length / 2)].t), padL + iw / 2, h - padB + 7);
    ctx.fillText(fmt(data[data.length - 1].t), w - padR - 14, h - padB + 7);

    this.series.forEach((key, si) => {
      const color = this.colors[key];
      const vals = data.map((d) => d[key]).filter((v) => v !== null && v !== undefined);
      if (vals.length < 2) return;

      // область под первой серией
      if (si === 0) {
        const grad = ctx.createLinearGradient(0, padT, 0, padT + ih);
        grad.addColorStop(0, color + "40");
        grad.addColorStop(1, color + "05");
        ctx.beginPath();
        let started = false;
        data.forEach((d, i) => {
          const v = d[key];
          if (v === null || v === undefined) return;
          const x = xAt(i);
          const y = yAt(v);
          if (!started) {
            ctx.moveTo(x, y);
            started = true;
          } else {
            ctx.lineTo(x, y);
          }
        });
        ctx.lineTo(xAt(data.length - 1), padT + ih);
        ctx.lineTo(padL, padT + ih);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();
      }

      // линия
      ctx.beginPath();
      let started = false;
      data.forEach((d, i) => {
        const v = d[key];
        if (v === null || v === undefined) return;
        const x = xAt(i);
        const y = yAt(v);
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.shadowColor = color;
      ctx.shadowBlur = si === 0 ? 8 : 0;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // точка на конце линии
      const lastVal = data[data.length - 1][key];
      if (lastVal !== null && lastVal !== undefined) {
        ctx.beginPath();
        ctx.arc(xAt(data.length - 1), yAt(lastVal), 3.2, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      }
    });
  }
}
