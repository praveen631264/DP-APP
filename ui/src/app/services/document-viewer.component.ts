import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { Document } from '../../services/document.service';

@Component({
  selector: 'app-document-viewer',
  templateUrl: './document-viewer.component.html',
  styleUrls: ['./document-viewer.component.scss']
})
export class DocumentViewerComponent implements OnChanges {
  @Input() document: Document | null = null;

  downloadUrl: string | null = null;
  previewUrl: SafeResourceUrl | null = null;
  isPdf = false;

  constructor(private sanitizer: DomSanitizer) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['document'] && this.document) {
      this.downloadUrl = `/api/v1/documents/${this.document._id}/download`;
      this.isPdf = this.document.content_type === 'application/pdf';

      if (this.isPdf) {
        this.previewUrl = this.sanitizer.bypassSecurityTrustResourceUrl(this.downloadUrl);
      }
    }
  }
}