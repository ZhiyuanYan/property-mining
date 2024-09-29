module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] c
);

    always@(posedge clk) begin
        $display("c: %b", c);
    end 


    
    always @(posedge clk) begin
        if(rst)begin
            c<=0;
        end
        else begin
                if (c!=200) begin
                    c<=c+1;
                end
                else if(c==40)begin
                        c<=1;
                end
            end
        end
    
    // assert property ((c==200)||(c>=0&&c<200));
endmodule