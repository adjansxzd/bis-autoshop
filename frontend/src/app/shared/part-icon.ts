import { Component, input } from '@angular/core';

/** Simple line icons per category (no external images → works offline on exam day). */
@Component({
  selector: 'app-part-icon',
  template: `
    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" [attr.width]="size()" [attr.height]="size()">
      @switch (name()) {
        @case ('disc') { <circle cx="24" cy="24" r="18"/><circle cx="24" cy="24" r="6"/><path d="M24 6v6M24 36v6M6 24h6M36 24h6"/> }
        @case ('droplet') { <path d="M24 6c7 9 12 15 12 22a12 12 0 0 1-24 0c0-7 5-13 12-22z"/><path d="M18 30a6 6 0 0 0 6 6"/> }
        @case ('filter') { <path d="M8 10h32l-12 14v12l-8 4V24z"/> }
        @case ('bulb') { <path d="M18 34h12M20 40h8"/><path d="M24 6a11 11 0 0 0-7 19.5c1.3 1.1 2 2.6 2 4.5h10c0-1.9.7-3.4 2-4.5A11 11 0 0 0 24 6z"/> }
        @case ('spring') { <path d="M16 6h16M16 42h16M16 10l16 4-16 4 16 4-16 4 16 4-16 4 16 4"/> }
        @case ('wheel') { <circle cx="24" cy="24" r="18"/><circle cx="24" cy="24" r="10"/><circle cx="24" cy="24" r="2"/><path d="M24 14v8M24 26v8M14 24h8M26 24h8"/> }
        @default { <path d="M24 6l5.5 11.2 12.3 1.8-8.9 8.7 2.1 12.3L24 34.2 13 40l2.1-12.3-8.9-8.7 12.3-1.8z"/> }
      }
    </svg>
  `,
  styles: `:host { display: inline-flex; }`,
})
export class PartIcon {
  name = input<string>('star');
  size = input<number>(48);
}
