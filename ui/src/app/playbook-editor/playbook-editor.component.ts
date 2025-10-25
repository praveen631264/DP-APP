import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { Playbook, PlaybookService, PlaybookStep } from '../services/playbook.service';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { NgxGraphModule } from '@swimlane/ngx-graph';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-playbook-editor',
  templateUrl: './playbook-editor.component.html',
  styleUrls: ['./playbook-editor.component.scss'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, NgxGraphModule]
})
export class PlaybookEditorComponent implements OnInit {

  playbookForm: FormGroup;
  isNewPlaybook = true;
  playbookId: string | null = null;
  stepMetadata: any = {};

  // Graph properties
  nodes: any[] = [];
  links: any[] = [];
  update$: Subject<boolean> = new Subject();

  selectedStepIndex: number | null = null;

  stepIconMap: { [key: string]: string } = {
    llm_prompt: '🤖',
    search: '🔍',
    api_call: '📞',
    conditional: '🔀',
    for_each: '🔁',
    parallel: '⏯️',
    update_document: '📝',
    tool_using_llm: '🛠️',
    default: '⚙️'
  };

  stepColorMap: { [key: string]: string } = {
    llm_prompt: '#cce5ff',
    search: '#d4edda',
    api_call: '#f8d7da',
    conditional: '#fff3cd',
    for_each: '#e2e3e5',
    parallel: '#d1ecf1',
    update_document: '#d4edda',
    tool_using_llm: '#f5c6cb',
    default: '#f8f9fa'
  };

  // Helper to use Object.keys in the template
  objectKeys = Object.keys;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private playbookService: PlaybookService,
    private cd: ChangeDetectorRef
  ) {
    this.playbookForm = this.fb.group({
      name: ['', Validators.required],
      category_name: ['', Validators.required],
      final_status: ['Processed'],
      steps: this.fb.array([])
    });

    // When the steps change, update the graph
    this.steps.valueChanges.subscribe(() => this.updateGraph());
  }

  ngOnInit(): void {
    this.playbookId = this.route.snapshot.paramMap.get('id');
    this.isNewPlaybook = this.playbookId === 'new';

    this.playbookService.getStepMetadata().subscribe(data => {
      this.stepMetadata = data;
      if (!this.isNewPlaybook && this.playbookId) {
        this.loadPlaybook(this.playbookId);
      }
      this.cd.markForCheck(); // Manually trigger change detection
    });
  }

  loadPlaybook(id: string): void {
    this.playbookService.getPlaybook(id).subscribe(playbook => {
      this.playbookForm.patchValue({ 
        name: playbook.name, 
        category_name: playbook.category_name,
        final_status: playbook.final_status
      });
      playbook.steps.forEach(step => this.addStep(step.type, step, false));
      this.updateGraph();
    });
  }

  get steps(): FormArray {
    return this.playbookForm.get('steps') as FormArray;
  }

  addStep(stepType: string, existingStep?: PlaybookStep, updateGraph = true): void {
    const stepMeta = this.stepMetadata[stepType];
    if (!stepMeta) return;

    const stepGroup = this.fb.group({
      type: [stepType, Validators.required],
      name: [existingStep?.name || stepMeta.name, Validators.required],
    });

    stepMeta.params.forEach((param: any) => {
      const value = existingStep ? existingStep[param.name] : param.default;
      const validators = param.required ? [Validators.required] : [];
      stepGroup.addControl(param.name, this.fb.control(value, validators));
    });

    this.steps.push(stepGroup);
    if (updateGraph) {
      this.updateGraph();
    }
  }

  removeStep(index: number): void {
    this.steps.removeAt(index);
    this.selectedStepIndex = null;
    this.updateGraph();
  }

  getStepParams(stepType: string): any[] {
    return this.stepMetadata[stepType]?.params || [];
  }

  updateGraph(): void {
    const nodes = [];
    const links = [];
    for (let i = 0; i < this.steps.length; i++) {
      const step = this.steps.at(i).value;
      nodes.push({
        id: `step_${i}`,
        label: step.name,
        data: {
          index: i,
          icon: this.stepIconMap[step.type] || this.stepIconMap['default'],
          color: this.stepColorMap[step.type] || this.stepColorMap['default']
        }
      });
      if (i > 0) {
        links.push({
          id: `link_${i-1}_${i}`,
          source: `step_${i-1}`,
          target: `step_${i}`
        });
      }
    }
    this.nodes = nodes;
    this.links = links;
    this.update$.next(true);
    this.cd.detectChanges();
  }

  onNodeClick(event: any): void {
    this.selectedStepIndex = event.data.index;
  }

  closeStepEditor(): void {
    this.selectedStepIndex = null;
  }

  get selectedStepFormGroup(): FormGroup {
    if (this.selectedStepIndex === null) {
      return null as any;
    }
    return this.steps.at(this.selectedStepIndex) as FormGroup;
  }

  savePlaybook(): void {
    if (this.playbookForm.valid) {
      const playbookData = this.playbookForm.value as Playbook;
      if (this.isNewPlaybook) {
        this.playbookService.createPlaybook(playbookData).subscribe(() => {
          this.router.navigate(['/playbooks']);
        });
      } else if (this.playbookId) {
        this.playbookService.updatePlaybook(this.playbookId, playbookData).subscribe(() => {
          this.router.navigate(['/playbooks']);
        });
      }
    }
  }
}
