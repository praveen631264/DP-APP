import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { WorkflowService } from '../services/workflow.service';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-stage-details-dialog',
  templateUrl: './stage-details-dialog.component.html',
  styleUrls: ['./stage-details-dialog.component.scss'],
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatSnackBarModule, MatButtonModule, MatIconModule]
})
export class StageDetailsDialogComponent implements OnInit, OnDestroy {

  logs: string = '';
  private intervalId: any;

  constructor(
    public dialogRef: MatDialogRef<StageDetailsDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private workflowService: WorkflowService,
    private snackBar: MatSnackBar,
    public dialog: MatDialog) { }

  ngOnInit(): void {
    this.logs = this.data.details.logs;
    this.intervalId = setInterval(() => {
      this.logs += `\n[${new Date().toLocaleTimeString()}] New log message...`;
    }, 2000);
  }

  ngOnDestroy(): void {
    clearInterval(this.intervalId);
  }

  onNoClick(): void {
    this.dialogRef.close();
  }

  retryProcess(process: any): void {
    this.workflowService.retryProcess(process.id).subscribe(() => {
      process.status = 'Running';
      this.snackBar.open(`Retrying process: ${process.name}`, 'Close', { duration: 3000 });
    });
  }

  stopProcess(process: any): void {
    this.workflowService.stopProcess(process.id).subscribe(() => {
      process.status = 'Stopped';
      this.snackBar.open(`Stopping process: ${process.name}`, 'Close', { duration: 3000 });
    });
  }

  pauseProcess(process: any): void {
    this.workflowService.pauseProcess(process.id).subscribe(() => {
      process.status = 'Paused';
      this.snackBar.open(`Pausing process: ${process.name}`, 'Close', { duration: 3000 });
    });
  }

  openAiAgent(process: any): void {
    this.dialog.open(AiAgentDialogComponent, {
      width: '80vw',
      height: '80vh',
      data: { process: process }
    });
  }
}
