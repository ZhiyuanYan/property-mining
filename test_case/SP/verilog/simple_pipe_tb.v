module simple_pipe_tb();

    // Generated top module signals
    reg  clk = 0;
    reg  rst = 0;
    reg  [7:0] inst;
    reg  [1:0] dummy_read_rf;
    reg  [7:0] dummy_rf_data;
    // wire outp;
    // wire overflw;

    // Generated top module instance
pipeline_v RTL(.clk(clk), 
               .rst(rst),
               .inst(inst), 
               .dummy_read_rf(dummy_read_rf), 
               .dummy_rf_data(dummy_rf_data) 
    );

    // Generated internal use signals
    // reg  [31:0] _conc_pc;
    // reg  [1:0] _conc_opcode;
    // reg  [1:0] _conc_ram[0:15];


    // Generated clock pulse
    always begin
        #5 clk = ~clk;
    end

    // initial begin 
    //     #20 rst = 0;
    // end

    initial begin
    // simulate 1000 cycles 
        for (int i = 0; i < 1000; i = i + 1) begin
            inst = {8{$random}};
            dummy_read_rf = {2{$random}};
            // dummy_rf_data = {8{$random}};
            #10;
        end
        
        $finish; // 结束仿真
    end
    // initial
    //   $monitor("At time %t, value = %h (%0d)",
    //           $time, inst, inst);

    initial
    begin            
        $dumpfile("wave.vcd");        //生成的vcd文件名称
        $dumpvars(0, RTL);    //tb模块名称
    end 
endmodule