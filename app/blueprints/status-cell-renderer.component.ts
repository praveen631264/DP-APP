import { Component } from '@angular/core';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import { ICellRendererParams } from 'ag-grid-community';

@Component({
  selector: 'app-status-cell-renderer',
  templateUrl: './status-cell-renderer.component.html',
  styleUrls: ['./status-cell-renderer.component.scss']
})
export class StatusCellRendererComponent implements ICellRendererAngularComp {
  
  public status!: string;
  public statusClass!: string;

  agInit(params: ICellRendererParams): void {
    this.status = params.value;
    this.statusClass = this.getClassForStatus(this.status);
  }

  refresh(params: ICellRendererParams): boolean {
    return false;
  }

  private getClassForStatus(status: string): string {
    const lowerStatus = status?.toLowerCase() || '';
    if (lowerStatus.includes('fail') || lowerStatus.includes('error')) return 'status-failed';
    if (lowerStatus.includes('complete') || lowerStatus.includes('processed')) return 'status-completed';
    if (lowerStatus.includes('process') || lowerStatus.includes('queued')) return 'status-processing';
    return 'status-default';
  }
}