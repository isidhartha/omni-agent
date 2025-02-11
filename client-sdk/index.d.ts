export interface OmniAgentOptions { host?: string; timeout?: number; }
export declare class OmniAgentClient {
  constructor(options?: OmniAgentOptions);
  runAgent(type: string, task: string, options?: object): Promise<any>;
  reviewPR(diff: string, context?: string): Promise<any>;
  debug(code: string, error: string): Promise<any>;
  analyzeRepo(path: string): Promise<any>;
  listAgents(): Promise<string[]>;
  health(): Promise<{ status: string }>;
}
export default OmniAgentClient;
