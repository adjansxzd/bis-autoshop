import { CUSTOM_ELEMENTS_SCHEMA, Component, OnInit, input, signal } from '@angular/core';

import { TPipe } from './t.pipe';

/**
 * Rotatable 3D model of a part (.glb) using Google's <model-viewer> web component.
 * The library (three.js inside) is loaded only when a 3D model is opened, so the rest of the site stays light.
 * Bundled from npm → works offline too.
 */
@Component({
  selector: 'app-part-model-3d',
  imports: [TPipe],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  template: `
    @if (ready()) {
      <model-viewer [attr.src]="src()" [attr.alt]="alt()" camera-controls auto-rotate auto-rotate-delay="1500"
                    rotation-per-second="20deg" interaction-prompt="none" shadow-intensity="0.8" exposure="1.05"
                    environment-image="neutral" camera-orbit="35deg 70deg auto" touch-action="pan-y"></model-viewer>
      <span class="hint">{{ 'model3d.hint' | t }}</span>
    } @else if (failed()) {
      <span class="msg">{{ 'model3d.failed' | t }}</span>
    } @else {
      <span class="msg">{{ 'catalog.loading' | t }}</span>
    }
  `,
  styles: `
    :host { position: absolute; inset: 0; display: grid; place-items: center; background: radial-gradient(circle at 50% 40%, var(--panel), var(--panel-2)); }
    model-viewer { width: 100%; height: 100%; --poster-color: transparent; }
    .hint { position: absolute; right: 12px; bottom: 12px; padding: 4px 8px; border-radius: 6px; background: rgba(0, 0, 0, .55); color: #fff; font-size: 11px; pointer-events: none; }
    .msg { color: var(--muted); font-size: 14px; }
  `,
})
export class PartModel3d implements OnInit {
  src = input.required<string>();
  alt = input('');
  ready = signal(false);
  failed = signal(false);

  ngOnInit() {
    import('@google/model-viewer').then(
      () => this.ready.set(true),
      () => this.failed.set(true),
    );
  }
}
