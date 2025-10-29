import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatPanelComponent } from '../chat-panel/chat-panel.component';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CategorizationDialogComponent } from '../categorization-dialog/categorization-dialog.component';

@Component({
  selector: 'app-document-viewer',
  templateUrl: './document-viewer.component.html',
  styleUrls: ['./document-viewer.component.scss'],
  standalone: true,
  imports: [CommonModule, ChatPanelComponent, MatDialogModule]
})
export class DocumentViewerComponent {

  constructor(public dialog: MatDialog) {}

  openCategorizationDialog(): void {
    const dialogRef = this.dialog.open(CategorizationDialogComponent, {
      width: '500px'
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('The dialog was closed');
    });
  }
}
