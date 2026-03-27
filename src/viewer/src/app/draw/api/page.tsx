import type React from 'react';
import { PAINT_API_SCHEMA, type ApiMethodDoc } from '@/lib/paintApiSchema';

export const metadata = {
  title: 'Programmer API — Paint by Language Model',
  description:
    'Complete API reference for window.paintByLanguageModel — programmatic canvas control for LLMs and automation scripts.',
};

/** Ordered categories with the method names that belong to each. */
const CATEGORIES: { title: string; methods: string[] }[] = [
  {
    title: 'Tool Config',
    methods: ['selectStrokeType', 'setColor', 'setOpacity', 'setThickness', 'setTypeParam'],
  },
  {
    title: 'Canvas Interactions',
    methods: ['click', 'doubleClick', 'cancelStroke'],
  },
  {
    title: 'Canvas Management',
    methods: [
      'clearCanvas',
      'getStrokes',
      'loadStrokes',
      'downloadJSON',
      'downloadJPG',
      'getCanvasImageDataUrl',
    ],
  },
  {
    title: 'Introspection',
    methods: ['getState', 'getStrokeTypes', 'getTypeParamSchema'],
  },
];

/** Quick-start snippet shown near the top of the page. */
const QUICK_START_SNIPPET = `// Open /draw in the browser, then paste this into the DevTools console:

const api = window.paintByLanguageModel;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// All tool-setting calls (selectStrokeType, setColor, setThickness, etc.) trigger
// async React state updates. Call all setters first, then await sleep(0) to let
// React flush them, then place your clicks.

await (async () => {
  // 1. Configure the tool
  api.selectStrokeType("line");
  api.setColor("#1a1a1a");
  api.setThickness(4);
  await sleep(50); // wait for all setters to flush before clicking

  // 2. Draw a line — click start point, then end point
  api.click(100, 300);
  api.click(700, 300);

  // Done! A horizontal line is now on the canvas.
})();`;

/** Worked example painted at the bottom of the page. */
const WORKED_EXAMPLE_SNIPPET = `// Sunset scene — horizon line, sun circle, sky splatters
// Canvas: 800 × 600 px  |  (0, 0) = top-left
//
// Tool-setting calls (selectStrokeType, setColor, setOpacity, setThickness) all
// trigger React state updates that are asynchronous. The correct pattern is:
//   1. Call all setters for a section
//   2. await sleep(50)  ← wait ~3 render frames for React to flush all queued state
//   3. Then place clicks
//
// sleep(0) / setTimeout(0) is NOT sufficient — React schedules renders via its
// own internal scheduler and may not have re-rendered the canvas component by
// the time a setTimeout(0) resolves. Use sleep(50) for reliable results.
//
// Two-click stroke types (line, arc, circle, splatter, burn, dodge) also need
// await sleep(50) between consecutive strokes of the same type, because the
// first stroke's commit triggers a React state update that must settle before
// the next stroke's first click can register correctly.

const api = window.paintByLanguageModel;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

await (async () => {

  // ── Sky background gradient effect (wide splatters) ────────────────────────
  // splatter = 2 clicks: centre point, then radius point
  api.selectStrokeType("splatter");
  api.setColor("#ffb347");      // warm orange
  api.setOpacity(0.6);
  api.setThickness(1);
  api.setTypeParam("splatter_count", 80);
  api.setTypeParam("dot_size_min", 3);
  api.setTypeParam("dot_size_max", 10);
  await sleep(50);
  api.click(400, 100);          // centre
  api.click(440, 100);          // radius point → commits splatter

  api.setColor("#ff6b6b");      // coral/red
  api.setOpacity(0.4);
  api.setTypeParam("splatter_count", 60);
  await sleep(50);               // flush colour change + wait for previous commit to settle
  api.click(200, 180);          // centre
  api.click(240, 180);          // radius point → commits splatter

  await sleep(50);
  api.click(600, 180);          // centre
  api.click(640, 180);          // radius point → commits splatter

  // ── Sun — filled yellow circle near horizon ─────────────────────────────────
  // circle = 2 clicks: centre point, then radius point
  api.selectStrokeType("circle");
  api.setColor("#ffe066");       // bright yellow
  api.setOpacity(1.0);
  api.setThickness(3);
  api.setTypeParam("fill", true);
  await sleep(50);
  api.click(400, 310);           // centre of sun
  api.click(450, 310);           // radius point (50 px radius)

  // ── Horizon line ────────────────────────────────────────────────────────────
  // line = 2 clicks: start point, then end point
  api.selectStrokeType("line");
  api.setColor("#cc3300");       // deep red horizon
  api.setOpacity(0.9);
  api.setThickness(3);
  await sleep(50);
  api.click(0, 360);             // left edge
  api.click(800, 360);           // right edge → commits line

  // ── Water / sea — horizontal wet-brush strokes below horizon ────────────────
  // wet-brush = multi-point: ≥2 clicks to add points, then doubleClick() to commit
  api.selectStrokeType("wet-brush");
  api.setColor("#1a3a5c");       // dark ocean blue
  api.setOpacity(0.8);
  api.setThickness(12);
  api.setTypeParam("softness", 4);
  api.setTypeParam("flow", 0.7);
  await sleep(50);
  api.click(0, 400);
  api.click(200, 395);
  api.click(400, 400);
  api.click(600, 395);
  api.doubleClick(800, 400);     // commits the stroke

  api.setOpacity(0.5);
  await sleep(50);
  api.click(0, 430);
  api.click(300, 425);
  api.click(600, 430);
  api.doubleClick(800, 430);

  // ── Sun reflection on water — three short vertical lines ────────────────────
  // Each line is 2 clicks. await sleep(0) between pairs so each commit settles
  // before the next stroke's first click fires.
  api.selectStrokeType("line");
  api.setColor("#ffe066");
  api.setOpacity(0.7);
  api.setThickness(2);
  await sleep(50);
  api.click(380, 365);
  api.click(380, 480);           // commits line 1
  await sleep(50);
  api.click(400, 365);
  api.click(400, 490);           // commits line 2
  await sleep(50);
  api.click(420, 365);
  api.click(420, 480);           // commits line 3

  // ── Atmospheric haze with burn ───────────────────────────────────────────────
  // burn = 2 clicks: start point, then end point
  api.selectStrokeType("burn");
  api.setThickness(80);
  api.setTypeParam("intensity", 0.15);
  await sleep(50);
  api.click(200, 360);           // left of horizon
  api.click(600, 360);           // right of horizon → commits burn

  // Done — a simple sunset is painted on the canvas.
  // Call window.paintByLanguageModel.getCanvasImageDataUrl() to export it.

})();`;

/**
 * Renders a single method's documentation card.
 *
 * @param {object} props - Component props
 * @param {string} props.name - Method name
 * @param {ApiMethodDoc} props.doc - Method documentation entry
 * @returns {React.JSX.Element} The rendered method card
 */
function MethodCard({ name, doc }: { name: string; doc: ApiMethodDoc }): React.JSX.Element {
  return (
    <div
      id={`method-${name}`}
      style={{
        border: '1px solid #ddd',
        borderRadius: '6px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
        background: '#fafafa',
      }}
    >
      {/* Signature */}
      <h4 style={{ fontFamily: 'monospace', fontSize: '1rem', marginBottom: '0.5rem' }}>{name}</h4>
      <pre
        style={{
          background: '#f0f0f0',
          padding: '0.5rem 0.75rem',
          borderRadius: '4px',
          fontSize: '0.85rem',
          overflowX: 'auto',
          marginBottom: '0.75rem',
        }}
      >
        <code>window.paintByLanguageModel.{doc.signature}</code>
      </pre>

      {/* Description */}
      <p style={{ marginBottom: '0.75rem' }}>{doc.description}</p>

      {/* Parameters table */}
      {doc.params.length > 0 && (
        <div style={{ marginBottom: '0.75rem' }}>
          <strong>Parameters</strong>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              marginTop: '0.4rem',
              fontSize: '0.875rem',
            }}
          >
            <thead>
              <tr style={{ background: '#e8e8e8' }}>
                <th
                  style={{ textAlign: 'left', padding: '0.3rem 0.5rem', border: '1px solid #ccc' }}
                >
                  Name
                </th>
                <th
                  style={{ textAlign: 'left', padding: '0.3rem 0.5rem', border: '1px solid #ccc' }}
                >
                  Type
                </th>
                <th
                  style={{ textAlign: 'left', padding: '0.3rem 0.5rem', border: '1px solid #ccc' }}
                >
                  Description
                </th>
              </tr>
            </thead>
            <tbody>
              {doc.params.map((param) => (
                <tr key={param.name}>
                  <td
                    style={{
                      padding: '0.3rem 0.5rem',
                      border: '1px solid #ccc',
                      fontFamily: 'monospace',
                    }}
                  >
                    {param.name}
                  </td>
                  <td
                    style={{
                      padding: '0.3rem 0.5rem',
                      border: '1px solid #ccc',
                      fontFamily: 'monospace',
                    }}
                  >
                    {param.type}
                  </td>
                  <td style={{ padding: '0.3rem 0.5rem', border: '1px solid #ccc' }}>
                    {param.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Return value */}
      {doc.returns !== undefined && (
        <p style={{ marginBottom: '0.75rem', fontSize: '0.875rem' }}>
          <strong>Returns:</strong> {doc.returns}
        </p>
      )}

      {/* Example */}
      <div>
        <strong>Example</strong>
        <pre
          style={{
            background: '#1e1e1e',
            color: '#d4d4d4',
            padding: '0.5rem 0.75rem',
            borderRadius: '4px',
            fontSize: '0.85rem',
            overflowX: 'auto',
            marginTop: '0.4rem',
          }}
        >
          <code>{doc.example}</code>
        </pre>
      </div>
    </div>
  );
}

/**
 * API documentation page for the window.paintByLanguageModel interface.
 *
 * A static Next.js server component — no JavaScript required to read the docs.
 * Content is generated from the PAINT_API_SCHEMA constant defined in paintApiSchema.ts.
 *
 * @returns {React.JSX.Element} The rendered documentation page
 */
export default function ApiDocsPage(): React.JSX.Element {
  return (
    <main
      style={{
        maxWidth: '860px',
        margin: '0 auto',
        padding: '2rem 1.5rem',
        fontFamily: 'system-ui, sans-serif',
        lineHeight: 1.6,
        color: '#1a1a1a',
      }}
    >
      {/* ── Page heading ─────────────────────────────────────────────────────── */}
      <h1 style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>
        Paint by Language Model — Programmer API
      </h1>
      <p style={{ color: '#555', marginBottom: '2rem' }}>
        <a href="/draw" style={{ color: '#0070f3' }}>
          ← Back to Draw
        </a>
      </p>

      {/* ── Canvas info ───────────────────────────────────────────────────────── */}
      <section
        style={{
          background: '#e8f4fd',
          border: '1px solid #b3d4f5',
          borderRadius: '6px',
          padding: '1rem 1.25rem',
          marginBottom: '2rem',
        }}
      >
        <h2 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Canvas</h2>
        <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
          <li>
            Size: <strong>800 × 600 pixels</strong>
          </li>
          <li>
            Background: <strong>white (#FFFFFF)</strong>
          </li>
          <li>
            Coordinate origin: <strong>(0, 0) = top-left corner</strong>; positive X goes right,
            positive Y goes down
          </li>
          <li>
            Bottom-right corner: <strong>(800, 600)</strong>
          </li>
        </ul>
      </section>

      {/* ── For LLMs intro ───────────────────────────────────────────────────── */}
      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.75rem' }}>For LLMs</h2>
        <p>
          This API allows a language model or external script to programmatically paint on the
          canvas by calling methods on <code>window.paintByLanguageModel</code> in the browser
          console, or in a Playwright / Puppeteer script aimed at the <code>/draw</code> page.
        </p>
        <p>
          The object is registered when the draw page mounts and removed when it unmounts.
          Tool-setting calls update the React state that backs the toolbar UI, so changes are
          reflected visually in real time.
        </p>
        <p>
          <strong>Scripted / Playwright contexts — async state:</strong> Tool-setting methods such
          as <code>selectStrokeType()</code>, <code>setColor()</code>, and{' '}
          <code>setThickness()</code> trigger React state updates, which are <em>asynchronous</em>.
          Always set all tool properties first, then <code>await sleep(50)</code> before placing
          clicks. <code>sleep(0)</code> is NOT reliable — React schedules renders via its own
          internal scheduler and may not have re-rendered the canvas component by the time a{' '}
          <code>setTimeout(0)</code> resolves. Use{' '}
          <code>{'const sleep = (ms) => new Promise(r => setTimeout(r, ms))'}</code> and{' '}
          <code>await sleep(50)</code> for consistent results.
        </p>
        <p>
          <strong>Clicks required per stroke type:</strong>
        </p>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            marginBottom: '1rem',
            fontSize: '0.875rem',
          }}
        >
          <thead>
            <tr style={{ background: '#e8e8e8' }}>
              <th style={{ textAlign: 'left', padding: '0.3rem 0.5rem', border: '1px solid #ccc' }}>
                Stroke type
              </th>
              <th style={{ textAlign: 'left', padding: '0.3rem 0.5rem', border: '1px solid #ccc' }}>
                Commits after
              </th>
            </tr>
          </thead>
          <tbody>
            {(
              [
                ['line, arc, burn, dodge', '2 clicks (start → end)'],
                ['circle, splatter', '2 clicks (centre → radius point)'],
                [
                  'polyline, dry-brush, chalk, wet-brush',
                  '≥2 clicks to add points, then doubleClick() to commit',
                ],
              ] as [string, string][]
            ).map(([types, rule]) => (
              <tr key={types}>
                <td
                  style={{
                    padding: '0.3rem 0.5rem',
                    border: '1px solid #ccc',
                    fontFamily: 'monospace',
                  }}
                >
                  {types}
                </td>
                <td style={{ padding: '0.3rem 0.5rem', border: '1px solid #ccc' }}>{rule}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* ── Quick-start ───────────────────────────────────────────────────────── */}
      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.75rem' }}>Quick Start</h2>
        <pre
          style={{
            background: '#1e1e1e',
            color: '#d4d4d4',
            padding: '1rem',
            borderRadius: '6px',
            fontSize: '0.875rem',
            overflowX: 'auto',
          }}
        >
          <code>{QUICK_START_SNIPPET}</code>
        </pre>
      </section>

      {/* ── Method reference ─────────────────────────────────────────────────── */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Method Reference</h2>

        {CATEGORIES.map((category) => (
          <section key={category.title} style={{ marginBottom: '2.5rem' }}>
            <h3
              style={{
                fontSize: '1.1rem',
                borderBottom: '2px solid #0070f3',
                paddingBottom: '0.3rem',
                marginBottom: '1rem',
              }}
            >
              {category.title}
            </h3>

            {category.methods.map((methodName) => {
              const doc = PAINT_API_SCHEMA[methodName];
              if (doc === undefined) return null;
              return <MethodCard key={methodName} name={methodName} doc={doc} />;
            })}
          </section>
        ))}
      </section>

      {/* ── Worked example ───────────────────────────────────────────────────── */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Worked Example — Sunset</h2>
        <p style={{ marginBottom: '0.75rem', color: '#555' }}>
          A complete script that paints a recognisable sunset scene. Copy-paste it into the DevTools
          console while the <code>/draw</code> page is open.
        </p>
        <pre
          style={{
            background: '#1e1e1e',
            color: '#d4d4d4',
            padding: '1rem',
            borderRadius: '6px',
            fontSize: '0.8rem',
            overflowX: 'auto',
            lineHeight: 1.5,
          }}
        >
          <code>{WORKED_EXAMPLE_SNIPPET}</code>
        </pre>
      </section>
    </main>
  );
}
