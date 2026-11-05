import { Component, OnInit, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { Product } from '../../core/models';
import { PartIcon } from '../../shared/part-icon';
import { KztPipe, LocPipe, TPipe } from '../../shared/t.pipe';

@Component({
  selector: 'app-product-detail',
  imports: [RouterLink, PartIcon, TPipe, LocPipe, KztPipe],
  templateUrl: './product-detail.html',
  styleUrl: './product-detail.scss',
})
export class ProductDetail implements OnInit {
  private api = inject(ApiService);
  id = input.required<string>(); // from route /product/:id (withComponentInputBinding)

  product = signal<Product | null>(null);
  error = signal(false);

  ngOnInit() {
    this.api.getProduct(Number(this.id())).subscribe({
      next: (p) => this.product.set(p),
      error: () => this.error.set(true),
    });
  }
}
