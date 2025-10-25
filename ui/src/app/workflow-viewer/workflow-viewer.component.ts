import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

interface WorkflowStep {
  name: string;
  status: string;
  // you can add other properties of a step here
}

@Component({
  selector: 'app-workflow-viewer',
  templateUrl: './workflow-viewer.component.html',
  styleUrls: ['./workflow-viewer.component.scss'],
  standalone: true,
  imports: [CommonModule],
})
export class WorkflowViewerComponent {
  @Input() steps: WorkflowStep[] = [];
}
