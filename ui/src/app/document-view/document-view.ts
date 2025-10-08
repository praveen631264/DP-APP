import { Component, Input } from '@angular/core';
import { Document } from '../document.service';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-document-view',
  templateUrl: './document-view.html',
  styleUrls: ['./document-view.scss'],
  standalone: true,
  imports: [CommonModule, MatCardModule]
})
export class DocumentView {
  @Input() document: Document | null | undefined;
}
