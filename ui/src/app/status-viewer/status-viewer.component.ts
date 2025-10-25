import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-status-viewer',
  templateUrl: './status-viewer.component.html',
  styleUrls: ['./status-viewer.component.scss'],
  standalone: true,
  imports: [CommonModule]
})
export class StatusViewerComponent {
  @Input() status: string = '';
}
