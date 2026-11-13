import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Header } from './components/header/header';
import { TPipe } from './shared/t.pipe';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header, TPipe],
  template: `
    <app-header />
    <router-outlet />
    <footer>{{ 'footer.text' | t }}</footer>
  `,
  styles: `footer { padding: 24px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; text-align: center; }`,
})
export class App {}
