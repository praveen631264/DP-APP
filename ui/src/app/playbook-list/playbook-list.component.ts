
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

// Angular Material Modules
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';

import { Playbook, PlaybookService } from '../services/playbook.service';
import { PlaybookEditorComponent } from '../playbook-editor/playbook-editor.component';

@Component({
  selector: 'app-playbook-list',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatListModule,
    MatIconModule,
    MatDialogModule,
    PlaybookEditorComponent
  ],
  templateUrl: './playbook-list.component.html',
  styleUrls: ['./playbook-list.component.scss']
})
export class PlaybookListComponent implements OnInit {
  playbooks: Playbook[] = [];

  constructor(
    private playbookService: PlaybookService,
    public dialog: MatDialog
  ) { }

  ngOnInit(): void {
    this.loadPlaybooks();
  }

  loadPlaybooks(): void {
    this.playbookService.getPlaybooks().subscribe(playbooks => {
      this.playbooks = playbooks;
    });
  }

  openPlaybookEditor(playbook?: Playbook): void {
    const dialogRef = this.dialog.open(PlaybookEditorComponent, {
      width: '800px',
      disableClose: true,
      data: { playbook: playbook }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        if (playbook?._id) {
          this.playbookService.updatePlaybook(playbook._id, result).subscribe(() => this.loadPlaybooks());
        } else {
          this.playbookService.createPlaybook(result).subscribe(() => this.loadPlaybooks());
        }
      }
    });
  }

  deletePlaybook(id: string | undefined): void {
    if (id) {
        this.playbookService.deletePlaybook(id).subscribe(() => {
            this.loadPlaybooks();
        });
    }
  }
}
