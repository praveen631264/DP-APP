import { Component, OnInit } from '@angular/core';
import { Node, Edge } from '@swimlane/ngx-graph';

// --- Interfaces for type safety ---
// Based on the mock data in the constructor.
// You might want to move these to a separate models file.
interface Step {
  id: string;
  name: string;
  type: string;
  next_step_id: string | null;
}

interface Playbook {
  id: string;
  name: string;
  steps: Step[];
}
// --- End Interfaces ---

@Component({
  selector: 'app-playbook-editor',
  templateUrl: './playbook-editor.component.html',
  styleUrls: ['./playbook-editor.component.scss']
})
export class PlaybookEditorComponent implements OnInit {

  nodes: Node[] = [];
  edges: Edge[] = [];
  playbook: Playbook; // Assuming you fetch this data

  // --- FIX: Add the missing map properties ---
  private readonly stepIconMap: { [key: string]: string } = {
    START: 'pi pi-play',
    ACTION: 'pi pi-cog',
    CONDITION: 'pi pi-question-circle',
    END: 'pi pi-stop-circle',
    'default': 'pi pi-question' // A default fallback
  };

  private readonly stepColorMap: { [key: string]: string } = {
    START: '#4CAF50',      // Green
    ACTION: '#2196F3',     // Blue
    CONDITION: '#FFC107',  // Amber
    END: '#F44336',        // Red
    'default': '#607D8B'   // A default fallback
  };

  constructor() { 
    // Mock playbook data for demonstration
    this.playbook = {
      id: 'pb-1',
      name: 'Sample Playbook',
      steps: [
        { id: 's1', name: 'Start Process', type: 'START', next_step_id: 's2' },
        { id: 's2', name: 'Perform Action', type: 'ACTION', next_step_id: 's3' },
        { id: 's3', name: 'Check Status', type: 'CONDITION', next_step_id: 's4' },
        { id: 's4', name: 'End Process', type: 'END', next_step_id: null },
      ],
    };
  }

  ngOnInit(): void {
    if (this.playbook) {
      this.updateGraph(this.playbook);
    }
  }

  updateGraph(playbook: Playbook): void {
    if (!playbook || !playbook.steps) {
      this.nodes = [];
      this.edges = [];
      return;
    }

    this.nodes = playbook.steps.map((step: Step) => ({
      id: step.id,
      label: step.name,
      data: {
        // This logic will now compile correctly
        icon: this.stepIconMap[step.type] || this.stepIconMap['default'],
        color: this.stepColorMap[step.type] || this.stepColorMap['default'],
      }
    }));

    this.edges = playbook.steps
      .filter(step => step.next_step_id)
      .map(step => ({
        id: `edge_${step.id}_${step.next_step_id}`,
        source: step.id,
        target: step.next_step_id!,
      }));
  }
}
