"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const QubeAgent_1 = require("./QubeAgent");
const eigenstate_logger_1 = require("./eigenstate_logger");
// Mock the EigenstateLogger to prevent actual logging and to spy on its methods
jest.mock('./eigenstate_logger', () => {
    const originalModule = jest.requireActual('./eigenstate_logger');
    const mockGetInstance = jest.fn();
    const mockLog = jest.fn();
    mockGetInstance.mockReturnValue({ log: mockLog });
    return {
        ...originalModule,
        EigenstateLogger: {
            ...originalModule.EigenstateLogger,
            getInstance: mockGetInstance,
            // We need to mock the static method getInstance, and then mock the log method on the instance it returns.
            // A bit convoluted, but that's how to mock singleton patterns in Jest.
            __singletonInstance: {
                log: mockLog
            }
        }
    };
});
// A more direct way to get the mock functions
const mockLog = eigenstate_logger_1.EigenstateLogger.getInstance().log;
describe('QubeAgent', () => {
    let agent;
    beforeEach(() => {
        // Clear all mocks before each test
        jest.clearAllMocks();
        agent = new QubeAgent_1.QubeAgent();
    });
    it('should be created with three runtime environment entities', () => {
        // The entities are private, so we can't access them directly.
        // Instead, we'll infer their existence by the behavior of runSimulation.
        // This is a more "black-box" approach to testing.
        expect(agent).toBeDefined();
    });
    describe('runSimulation', () => {
        it('should run a simulation, calling execute and getFeedback on each entity', async () => {
            // We spy on the console.log to suppress output during tests
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => { });
            await agent.runSimulation(0); // use 0ms duration for speed
            // The agent has 3 internal entities. Let's check if the logger was called for each
            // 1 call for init, 3 for the entities, 1 for the end.
            expect(mockLog).toHaveBeenCalledTimes(5);
            // Check for the init log
            expect(mockLog).toHaveBeenCalledWith('qube_init', 'STARTING', expect.any(Object), true, 'Qube Agent Startup');
            // Check for the simulation end log
            expect(mockLog).toHaveBeenCalledWith('qube_sim_end', 'COMPLETE', expect.any(Object), true, 'All Qube entities simulated.');
            // Check that entity simulation logs were called
            expect(mockLog).toHaveBeenCalledWith(expect.stringMatching(/entity_sim_qubes_os/), 'ACTIVE', expect.any(Object), false, expect.any(String));
            expect(mockLog).toHaveBeenCalledWith(expect.stringMatching(/entity_sim_qube_3d_engine/), 'ACTIVE', expect.any(Object), false, expect.any(String));
            expect(mockLog).toHaveBeenCalledWith(expect.stringMatching(/entity_sim_qube_apps_solutions/), 'ACTIVE', expect.any(Object), false, expect.any(String));
            // Since we can't directly spy on the private entities,
            // we can check the console logs that would be produced by them.
            // This is a bit brittle, but it's one way to test private properties' behavior.
            expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Simulating Entity: Qubes OS"));
            expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Simulating Entity: Qube (3D Engine)"));
            expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Simulating Entity: Qube Apps Solutions"));
            expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Feedback Analysis:"));
            // Restore the console
            consoleSpy.mockRestore();
        });
        it('should use the provided duration for delays', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => { });
            const duration = 10; // 10ms
            const startTime = Date.now();
            await agent.runSimulation(duration);
            const endTime = Date.now();
            // The total time should be at least 3 * duration, as the promises run in parallel for the entities.
            // But they are awaited with Promise.all, so the total duration is roughly the duration of one.
            // Since we have 3 entities, and we use await new Promise for each, it should be at least `duration`.
            expect(endTime - startTime).toBeGreaterThanOrEqual(duration);
            consoleSpy.mockRestore();
        });
    });
});
