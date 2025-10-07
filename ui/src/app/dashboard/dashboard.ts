import { Component, inject } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import { AsyncPipe, NgFor } from '@angular/common';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatMenuModule } from '@angular/material/menu';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss'],
  standalone: true,
  imports: [
    AsyncPipe,
    NgFor,
    MatGridListModule,
    MatMenuModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule
  ]
})
export class Dashboard {
  private breakpointObserver = inject(BreakpointObserver);

  /** Based on the screen size, switch from standard to one column per row. */
  cards = this.breakpointObserver.observe(Breakpoints.Handset).pipe(
    map(({ matches }) => {
      if (matches) {
        return [
          { title: 'Card 1', cols: 1, rows: 1, content: 'Card 1 content' },
          { title: 'Card 2', cols: 1, rows: 1, content: 'Card 2 content' },
          { title: 'Card 3', cols: 1, rows: 1, content: 'Card 3 content' },
          { title: 'Card 4', cols: 1, rows: 1, content: 'Card 4 content' }
        ];
      }

      return [
        { title: 'Card 1', cols: 2, rows: 1, content: 'Card 1 content' },
        { title: 'Card 2', cols: 1, rows: 1, content: 'Card 2 content' },
        { title: 'Card 3', cols: 1, rows: 2, content: 'Card 3 content' },
        { title: 'Card 4', cols: 1, rows: 1, content: 'Card 4 content' }
      ];
    })
  );

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );
}
